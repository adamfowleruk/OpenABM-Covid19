/*
 * disease.c


 *
 *  Created on: 18 Mar 2020
 *      Author: hinchr
 */

#include "model.h"
#include "individual.h"
#include "utilities.h"
#include "constant.h"
#include "contact_event.h"
#include "params.h"
#include "network.h"
#include "disease.h"
#include "structure.h"
#include "interventions.h"
#include <stdio.h>
#include <stdlib.h>
#include <math.h>

/*****************************************************************************************
*  Name:		estimate_mean_interactions_by_age
*  Description: estimates the weighted mean number of interactions by age
*  				each interaction is weighted by the type factor
*
* 	Argument:  age - integer of the age group, if age == -1 then include everyone
*
*  Returns:		void
******************************************************************************************/
double estimate_mean_interactions_by_age( model *model, int age )
{
	long pdx, ndx;
	long people = 0;
	double inter  = 0;
	double *weight = model->params->relative_transmission;

	for( pdx = 0; pdx < model->params->n_total; pdx++ )
		if( ( model->population[pdx].age_type == age ) | ( age == -1 ) )
		{
			people++;
			inter += model->population[pdx].base_random_interactions * weight[RANDOM];
		}

	for( pdx = 0; pdx < model->household_network->n_edges; pdx++ )
	{
		if( ( model->population[model->household_network->edges[pdx].id1].age_type == age ) | ( age == -1 ) )
			inter += weight[HOUSEHOLD];
		if( ( model->population[model->household_network->edges[pdx].id2].age_type == age ) | ( age == -1 ))
			inter += weight[HOUSEHOLD];
	}

	for( ndx = 0; ndx < model->n_occupation_networks ; ndx++ )
		for( pdx = 0; pdx < model->occupation_network[ndx]->n_edges; pdx++ )
		{
			if( ( model->population[model->occupation_network[ndx]->edges[pdx].id1].age_type == age ) | ( age == -1 ))
				inter += model->params->daily_fraction_work * weight[OCCUPATION];
			if( ( model->population[model->occupation_network[ndx]->edges[pdx].id2].age_type == age  ) | ( age == -1 ))
				inter  += model->params->daily_fraction_work * weight[OCCUPATION];
		}

	return 1.0 * inter / people;
}

/*****************************************************************************************
*  Name:		set_up_infectious curves
*  Description: sets up discrete distributions and functions which are used to
*  				model events and calculates infectious rate per interaction.
*
*				If relative susceptibility by age is a per interaction measure, then
*  				the infectious rate is adjusted by the total mean interactions.
*
*				If relative susceptibility by age is a per day measure, then
*				the infectious rate per interaction adult is the infectious rate divided
*  				by the mean number of daily interactions of an adult. Adjustments are calculated
*  				for children and elderly based upon their difference in the number of daily
*  				interactions and the relative overall susceptibility.
*
*  Returns:		void
******************************************************************************************/
void set_up_infectious_curves( model *model )
{
	parameters *params = model->params;
	double infectious_rate;
	int group;

	infectious_rate = params->infectious_rate;
	if( params->relative_susceptibility_by_interaction )
	{
		if( model->mean_interactions > 0 )
			infectious_rate /= model->mean_interactions;
		for( group = 0; group < N_AGE_GROUPS; group++ )
			params->adjusted_susceptibility[group] = params->relative_susceptibility[group];
	}
	else
	{
		infectious_rate /= model->mean_interactions_by_age[AGE_TYPE_ADULT];

		for( group = 0; group < N_AGE_GROUPS; group++ )
			params->adjusted_susceptibility[group] = params->relative_susceptibility[group] * model->mean_interactions_by_age[AGE_TYPE_ADULT] / model->mean_interactions_by_age[AGE_TYPE_MAP[group]];
	}
	params->infectious_rate_adjusted = infectious_rate;
}
/*****************************************************************************************
*  Name:		transmit_virus_by_type
*  Description: Transmits virus over the interaction network for a type of
*  				infected people
*  Returns:		void
******************************************************************************************/
void transmit_virus_by_type(
	model *model,
	int type
)
{
	long idx, jdx, n_infected, strain_idx;
	int day, n_interaction, t_infect;
	double hazard_rate, infector_mult, infector_progression_mult, network_mult, contact_hazard;
	event_list *list = &(model->event_lists[type]);
	event *event, *next_event;
	interaction *interaction;
	individual *infector;
	int rebuild_networks = model->params->rebuild_networks;
	double *infectious_curve;

	contact_event* ce;

	for( day = model->time-1; day >= max( 0, model->time - MAX_INFECTIOUS_PERIOD ); day-- )
	{
		n_infected  = list->n_daily_current[ day ];
		next_event  = list->events[ day ];

		for( idx = 0; idx < n_infected; idx++ )
		{
			event      = next_event;
			next_event = event->next;
			infector   = event->individual;

			t_infect = model->time - time_infected_infection_event( infector->infection_events );
			if( t_infect >= MAX_INFECTIOUS_PERIOD )
				continue;

			n_interaction = infector->n_interactions[ model->interaction_day_idx ];
			if( n_interaction > 0 )
			{
				interaction   = infector->interactions[ model->interaction_day_idx ];
				infector_mult = infector->infectiousness_multiplier * infector->infection_events->strain->transmission_multiplier;
				strain_idx 	  = infector->infection_events->strain->idx;
				infectious_curve = infector->infection_events->strain->infectious_curve[type];
				infector_progression_mult = infectious_curve[ t_infect - 1 ];

				for( jdx = 0; jdx < n_interaction; jdx++ )
				{
					if( !rebuild_networks )
					{
						if( infector->house_no != interaction->individual->house_no &&
							( infector->quarantined || interaction->individual->quarantined ) )
						{
							interaction = interaction->next;
							continue;
						}
					}

					if( interaction->individual->status == SUSCEPTIBLE )
					{
						if( immune_full( interaction->individual, strain_idx ) ) {
							interaction = interaction->next;
							continue;
						}

						network_mult  = model->all_networks[ interaction->network_id ]->transmission_multiplier_combined;

						ce = calloc(1,sizeof(contact_event));
						ce->source_id = infector->idx;
						ce->contact_id = interaction->individual->idx;
						ce->day = day;
						ce->was_infected = FALSE;
						ce->network_id = interaction->network_id;
						ce->next = NULL;
						ce->duration_minutes = 0.0;
						
						// Contact hazard calculation
						// Method 1: Default OpenABM-Covid19 infection model
						contact_hazard = infector_progression_mult * infector_mult;
						// Note: The above only needs to be done once, rather than for every interaction

						// Method 2: Based on duration of the contact event only
						ce->duration_minutes = get_duration(model, interaction); // Select duration from a distribution
						contact_hazard *= get_duration_hazard(ce->duration_minutes, model, interaction); // Based on duration, the chance of infection
						// Note we're still multiplying here as total duration is < 24 hours whereas contacts and disease progression can happen every day
						// Note by default the above returns 0.0 for duration and 1.0 for duration hazard, respectively

						hazard_rate = contact_hazard * network_mult;

						// Set CE threshold and score before we decrement the hazard
						ce->susceptibility = interaction->individual->original_hazard[ strain_idx ];
						ce->risk_threshold = interaction->individual->hazard[ strain_idx ];
						ce->risk_evaluation = hazard_rate;

						// Now reduce the individuals current hazard rate
						interaction->individual->hazard[ strain_idx ] -= hazard_rate;

						if( interaction->individual->hazard[ strain_idx ] < 0 )
						{
							new_infection( model, interaction->individual, infector, interaction->network_id, infector->infection_events->strain );
							interaction->individual->infection_events->infector_network = interaction->type;
							ce->was_infected = TRUE;
						}
						if (NULL == model->contact_events) {
							model->contact_events = ce;
							model->last_contact_event = ce;
						} else {
							model->last_contact_event->next = ce;
							model->last_contact_event = ce;
						}
					}
					interaction = interaction->next;
				}
			}
		}
	}
}

/*****************************************************************************************
*  Name:		transmit_virus
*  Description: Transmits virus over the interaction network
*
*  				Transmission by groups depending upon disease status.
*  				Note that quarantine is not a disease status and they will either
*  				be presymptomatic/symptomatic/asymptomatic and quarantining is
*  				modelled by reducing the number of interactions in the network.
*
*  Returns:		void
******************************************************************************************/
void transmit_virus( model *model )
{
	transmit_virus_by_type( model, PRESYMPTOMATIC );
	transmit_virus_by_type( model, PRESYMPTOMATIC_MILD );
	transmit_virus_by_type( model, SYMPTOMATIC );
	transmit_virus_by_type( model, SYMPTOMATIC_MILD );
	transmit_virus_by_type( model, ASYMPTOMATIC );
	transmit_virus_by_type( model, HOSPITALISED );
	transmit_virus_by_type( model, CRITICAL );
	transmit_virus_by_type( model, HOSPITALISED_RECOVERING );
}

/*****************************************************************************************
*  Name:		seed_infect_by_idx
*  Description: infects a new individual from an external source
*  Returns:		void
******************************************************************************************/
short seed_infect_by_idx(
	model *model,
	long pdx,
	int strain_idx,
	int network_id
)
{
	individual *infected = &(model->population[ pdx ]);

	if( ( infected->status != SUSCEPTIBLE ) || ( infected->hazard[ strain_idx ] < 0 ) )
		return FALSE;

	if( strain_idx >= model->n_initialised_strains )
		print_exit( "strain_idx is not known, strains must be initialised before being infected" );

	new_infection( model, infected, infected, network_id,  &(model->strains[ strain_idx ]) );
	return TRUE;
}

/*****************************************************************************************
*  Name:		seed_infect_n_people
*  Description: infects multiple people from an external source
*  Returns:		void
******************************************************************************************/
long seed_infect_n_people(
	model *model,
	long n_to_infect,
	int strain_idx,
	int network_id
)
{
	long n_infected, idx, pdx, n_total;
	n_infected = 0;
	n_total    = model->params->n_total;

	for( idx = 0; idx < n_to_infect; idx++ )
	{
		pdx = gsl_rng_uniform_int( rng, n_total );
		n_infected += seed_infect_by_idx( model, pdx, strain_idx, network_id );
	}

	return( n_infected );
}

/*****************************************************************************************
*  Name:		new_infection
*  Description: infects a new individual from another individual
*  Returns:		void
******************************************************************************************/
void new_infection(
	model *model,
	individual *infected,
	individual *infector,
	int network_id,
	strain *strain
)
{
	double draw       = gsl_rng_uniform( rng );
	double asymp_frac = strain->fraction_asymptomatic[infected->age_group];
	double mild_frac  = strain->mild_fraction[infected->age_group];

	if( immune_to_symptoms( infected, strain->idx ) )
		asymp_frac = 1;

	add_infection_event( infected, infector, network_id, strain, model->time );
	strain->total_infected++;

	if( draw < asymp_frac )
	{
		transition_one_disese_event( model, infected, SUSCEPTIBLE, ASYMPTOMATIC, NO_EDGE );
		transition_one_disese_event( model, infected, ASYMPTOMATIC, RECOVERED, ASYMPTOMATIC_RECOVERED );
	}
	else if( draw < asymp_frac + mild_frac )
	{
		transition_one_disese_event( model, infected, SUSCEPTIBLE, PRESYMPTOMATIC_MILD, NO_EDGE );
		transition_one_disese_event( model, infected, PRESYMPTOMATIC_MILD, SYMPTOMATIC_MILD, PRESYMPTOMATIC_MILD_SYMPTOMATIC_MILD );
	}
	else
	{
		transition_one_disese_event( model, infected, SUSCEPTIBLE, PRESYMPTOMATIC, NO_EDGE );
		transition_one_disese_event( model, infected, PRESYMPTOMATIC, SYMPTOMATIC, PRESYMPTOMATIC_SYMPTOMATIC );
	}

	if( !immune_to_symptoms( infected, strain->idx ) && !immune_to_severe( infected, strain->idx ) )
		infected->infection_events->expected_hospitalisation = strain->hospitalised_fraction[ infected->age_group ] * ( 1 - asymp_frac - mild_frac );
}

/*****************************************************************************************
*  Name:		transition_one_disease_event
*  Description: Generic function for updating an individual with their next
*				event and adding the applicable events
*  Returns:		void
******************************************************************************************/
void transition_one_disese_event(
	model *model,
	individual *indiv,
	int from,
	int to,
	int edge
)
{
	indiv->status           = from;

	if( (from != NO_EVENT) | (from != SUSCEPTIBLE))
		indiv->infection_events->times[from] = model->time;
	if( indiv->current_disease_event != NULL )
		remove_event_from_event_list( model, indiv->current_disease_event );
	if( indiv->next_disease_event != NULL )
		indiv->current_disease_event = indiv->next_disease_event;

	if( indiv->quarantined == TRUE){
		if(from == SUSCEPTIBLE){
			model->n_quarantine_infected++;
			if(indiv->app_user == TRUE){
				model->n_quarantine_app_user_infected++;
			}
		}
	}

	if( to != NO_EVENT )
	{
		indiv->infection_events->times[to]     = model->time + ifelse( edge == NO_EDGE, 0, sample_transition_time( indiv->infection_events->strain, edge ) );
		indiv->next_disease_event = add_individual_to_event_list( model, to, indiv, indiv->infection_events->times[to], NULL );
	}
}

/*****************************************************************************************
*  Name:		transition_to_symptomatic
*  Description: Transitions infected who are due to become symptomatic. At this point
*  				there are 2 choices to be made:
*
*  				1. Will the individual require hospital treatment or will
*  				they recover without needing treatment
*  				2. Does the individual self-quarantine at this point and
*  				asks for a test
*
*  Returns:		void
******************************************************************************************/
void transition_to_symptomatic( model *model, individual *indiv )
{
 	strain *strain = indiv->infection_events->strain;

	if( immune_to_severe( indiv, strain->idx ) ) {
		transition_one_disese_event( model, indiv, SYMPTOMATIC, RECOVERED, SYMPTOMATIC_RECOVERED );
	} else
	{
		if( gsl_ran_bernoulli( rng, strain->hospitalised_fraction[ indiv->age_group ] ) )
			transition_one_disese_event( model, indiv, SYMPTOMATIC, HOSPITALISED, SYMPTOMATIC_HOSPITALISED );
		else
			transition_one_disese_event( model, indiv, SYMPTOMATIC, RECOVERED, SYMPTOMATIC_RECOVERED );
	}

	intervention_on_symptoms( model, indiv );
}

/*****************************************************************************************
*  Name:		transition_to_symptomatic_mild
*  Description: Transitions infected who are due to become symptomatic with mild symptoms.
*
*  				1. Add the recovery event
*  				2. Does the individual self-quarantine at this point and
*  				asks for a test
*
*  Returns:		void
******************************************************************************************/
void transition_to_symptomatic_mild( model *model, individual *indiv )
{
	transition_one_disese_event( model, indiv, SYMPTOMATIC_MILD, RECOVERED, SYMPTOMATIC_MILD_RECOVERED );
	intervention_on_symptoms( model, indiv );
}

/*****************************************************************************************
*  Name:		transition_to_hospitalised
*  Description: Transitions symptomatic individual to a severe disease state, and assigns them
*               to a hospital for upcoming hospital states.
*  Returns:		void
******************************************************************************************/
void transition_to_hospitalised( model *model, individual *indiv )
{
	set_hospitalised( indiv, model->params, model->time );
 	strain *strain = indiv->infection_events->strain;

	if( model->params->hospital_on )
	{
		int assigned_hospital_idx = find_least_full_hospital( model, COVID_GENERAL );
		add_patient_to_waiting_list( indiv, &(model->hospitals[assigned_hospital_idx]), COVID_GENERAL );
	}
	else
	{
		model->event_lists[TRANSITION_TO_HOSPITAL].n_daily_current[model->time]+=1;
		model->event_lists[TRANSITION_TO_HOSPITAL].n_total+=1;

		if( gsl_ran_bernoulli( rng, strain->critical_fraction[ indiv->age_group ] ) )
		{
			if( gsl_ran_bernoulli( rng, strain->location_death_icu[ indiv->age_group ] ) )
				transition_one_disese_event( model, indiv, HOSPITALISED, CRITICAL, HOSPITALISED_CRITICAL );
			else
				transition_one_disese_event( model, indiv, HOSPITALISED, DEATH, HOSPITALISED_CRITICAL );
			}
		else
			transition_one_disese_event( model, indiv, HOSPITALISED, RECOVERED, HOSPITALISED_RECOVERED );
	}

	if( indiv->quarantined )
		intervention_quarantine_release( model, indiv );

	intervention_on_hospitalised( model, indiv );
}

/*****************************************************************************************
*  Name:		transition_to_critical
*  Description: Transitions hopsitalised individual to critical care
*  Returns:		void
******************************************************************************************/
void transition_to_critical( model *model, individual *indiv )
{
	set_critical( indiv, model->params, model->time );
 	strain *strain = indiv->infection_events->strain;

	if( model->params->hospital_on )
	{
		remove_if_in_waiting_list(indiv, &model->hospitals[indiv->hospital_idx]);
		add_patient_to_waiting_list( indiv, &(model->hospitals[indiv->hospital_idx]), COVID_ICU );
	}
	else
	{
		model->event_lists[TRANSITION_TO_CRITICAL].n_daily_current[model->time]+=1;
		model->event_lists[TRANSITION_TO_CRITICAL].n_total+=1;

		if( gsl_ran_bernoulli( rng, strain->fatality_fraction[ indiv->age_group ] ) )
			transition_one_disese_event( model, indiv, CRITICAL, DEATH, CRITICAL_DEATH );
		else
			transition_one_disese_event( model, indiv, CRITICAL, HOSPITALISED_RECOVERING, CRITICAL_HOSPITALISED_RECOVERING );
	}

	intervention_on_critical( model, indiv );

}

/*****************************************************************************************
*  Name:		transition_to_hospitalised_recovering
*  Description: Transitions out of critical those who survive
*  Returns:		void
******************************************************************************************/
void transition_to_hospitalised_recovering( model *model, individual *indiv )
{
	if( model->params->hospital_on )
	{
		remove_if_in_waiting_list( indiv, &model->hospitals[indiv->hospital_idx] );
		if( indiv->ward_type != COVID_GENERAL )
			add_patient_to_waiting_list( indiv, &model->hospitals[indiv->hospital_idx], COVID_GENERAL );
	}

	transition_one_disese_event( model, indiv, HOSPITALISED_RECOVERING, RECOVERED, HOSPITALISED_RECOVERING_RECOVERED );
	set_hospitalised_recovering( indiv, model->params, model->time );
}

/*****************************************************************************************
*  Name:		transition_to_recovered
*  Description: Transitions hospitalised and asymptomatic to recovered
*  Returns:		void
******************************************************************************************/
void transition_to_recovered( model *model, individual *indiv )
{
	int strain_idx = indiv->infection_events->strain->idx;
	int time_susceptible, complete_immunity;

	if( model->params->hospital_on )
	{
		if( indiv->hospital_state != NOT_IN_HOSPITAL )
		{
			remove_if_in_waiting_list( indiv, &model->hospitals[indiv->hospital_idx] );
			transition_one_hospital_event( model, indiv, indiv->hospital_state, DISCHARGED, NO_EDGE );
		}
	}

	transition_one_disese_event( model, indiv, RECOVERED, SUSCEPTIBLE, RECOVERED_SUSCEPTIBLE );

	time_susceptible  = indiv->infection_events->times[ SUSCEPTIBLE ];

	complete_immunity = apply_cross_immunity( model, indiv, strain_idx, time_susceptible );
	set_recovered( indiv, model->params, model->time, model );

	if( !complete_immunity ) {
	    set_susceptible( indiv, model->params, model->time );
	    indiv->current_disease_event = NULL;
	    indiv->next_disease_event = NULL;
	}
}

/*****************************************************************************************
*  Name:		apply_cross_immunity
*  Description: Apply's whether cross-immunity is confered to the other strains based upon
*  				the polarising cross-immunity model (all or nothing).
*
*  				Further, we assume complete correlation in cross-immunity, whereby we draw
*  				a single U(0,1) variable and all entries in cross-immunity matrix with
*  				correlation greater than this will have immunity
*
*  Returns:		void
******************************************************************************************/
short apply_cross_immunity( model *model, individual *indiv, short strain_idx, short time_susceptible )
{
	short complete_immunity = TRUE;
	short sdx;
	float *cross_immunity = model->cross_immunity[ strain_idx ];
	float r_unif = gsl_rng_uniform( rng );

	for( sdx = 0; sdx < model->params->max_n_strains; sdx++ )
	{
		if( ( sdx == strain_idx ) || ( cross_immunity[ sdx ] > r_unif ) ) {
			set_immune( indiv, sdx, time_susceptible, IMMUNE_FULL );
		} else
			complete_immunity = FALSE;
	}

	return complete_immunity;
}

/*****************************************************************************************
*  Name:        transition_to_susceptible
*  Description: Transitions recovered to susceptible
*  Returns:     void
******************************************************************************************/
void transition_to_susceptible( model *model, individual *indiv )
{
	// set susceptible needs to know current state, so set on the individual first
	set_susceptible( indiv, model->params, model->time );
}


/*****************************************************************************************
*  Name:		transition_to_death
*  Description: Transitions hospitalised to death
*  Returns:		void
******************************************************************************************/
void transition_to_death( model *model, individual *indiv )
{
	if( model->params->hospital_on )
	{
		if( !not_in_hospital(indiv) )
		{
			remove_if_in_waiting_list( indiv, &model->hospitals[indiv->hospital_idx] );
			transition_one_hospital_event( model, indiv, indiv->hospital_state, MORTUARY, NO_EDGE );
		}
	}

	transition_one_disese_event( model, indiv, DEATH, NO_EVENT, NO_EDGE );
	set_dead( indiv, model->params, model->time );
}

/*****************************************************************************************
*  Name:		n_newly_infected
*  Description: Calculates the total nubmber of newly infected people on a day
*  Returns:		long
******************************************************************************************/
long n_newly_infected( model *model, int time )
{
	if( time > model->time )
		return ERROR;

	int idx;
	long total = 0;

	for( idx = 0; idx < N_NEWLY_INFECTED_STATES; idx++ )
		total += n_total_by_day( model, NEWLY_INFECTED_STATES[ idx], time );

	return total;
}

/*****************************************************************************************
*  Name:		calculate_R_instanteous
*  Description: Calculates the instantaneous value of R using time-series of known infections
*  				and the known generation time distribution
*
*  				percentile is the value of the posterior distribution e.g. 0.5 is the median
*
*  Returns:		double
******************************************************************************************/
double calculate_R_instanteous( model *model, int time, double percentile )
{
	if( ( time > model->time ) || ( percentile <= 0 ) || ( percentile >= 1 ) )
		return ERROR;

	int day;
	double expected_infections = 0;
	long actual_infections     = n_newly_infected( model, time );
	double *generation_dist    = calloc( MAX_INFECTIOUS_PERIOD, sizeof(double) );

	gamma_rate_curve( generation_dist, MAX_INFECTIOUS_PERIOD, model->params->mean_infectious_period, model->params->sd_infectious_period, 1);

	day = time-1;
	while( ( day >= 0 ) & ( ( time - day ) < MAX_INFECTIOUS_PERIOD ) )
	{
		expected_infections += generation_dist[ time - day - 1 ] * n_newly_infected( model, day );
		day--;
	}

	free( generation_dist );

	if( ( actual_infections <= 1 ) || ( expected_infections <= 1 ) )
		return ERROR;

	return inv_incomplete_gamma_p( percentile, actual_infections ) / expected_infections;
}

/*****************************************************************************************
*  Name:		set_cross_immunity_probability
*  Description: --
*  Returns:		void
******************************************************************************************/
void set_cross_immunity_probability( 
	model *model, 
	int caught_idx, 
	int conferred_idx, 
	float probability 
)
{
	model->cross_immunity[ caught_idx ][ conferred_idx ] = probability;
}
