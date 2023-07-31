/*
 * incontact_eventput.c
 *
 *  Created on: 7 Dec 2022
 *      Author: Adam Fowler <adam@adamfowler.org> <adam.fowler@spc.ox.ac.uk>
 */



#include "contact_event.h"
#include "constant.h"
#include "model.h"
#include "individual.h"


/*****************************************************************************************
*  Name:		get_contact_events
*  Description: Return all contact events (Interaction instances) in the model since a
*               specified time (inclusive).
*               Caller owns the pointer.
******************************************************************************************/
contact_events_summary* get_contact_events( model* model, int since )
{
	// long idx, jdx, n_infected;
	// int day, n_interaction, t_infect;
	// event_list *list = &(model->event_lists[SYMPTOMATIC]); // TODO make this dynamic
	// event *event, *next_event;
	// interaction *interaction;
	// individual *infector;

    long count = 0;

    contact_event* first = NULL;
    contact_event* last = NULL;

    // // generate dummy event for testing
    // contact_event* new_event = calloc( 1, sizeof( contact_event ) );
    // new_event->day = model->time;
    // new_event->source_id = list->n_daily_current[ 2 ];
    // if (0 != new_event->source_id) {
    //     new_event->contact_id = list->events[ day ]->individual->idx;
    // } else {
    //     new_event->contact_id = 2;
    // }
    // new_event->network_id = 3;
    // new_event->was_infected = FALSE; // We set this from Transmissions, later
    // ++count;

    // first = new_event;
    // last = new_event;

    // // Loop over all Interactions from INFECTORS
    // // individual* indiv = model->population;

	// // for( day = model->time-1; day >= max( 0, model->time - MAX_INFECTIOUS_PERIOD ); day-- )
	// for( day = 1; day <= model->time; ++day )
	// {
	// 	n_infected  = list->n_daily_current[ day ];
	// 	next_event  = list->events[ day ];

	// 	for( idx = 0; idx < n_infected; idx++ )
	// 	{
	// 		event      = next_event;
	// 		next_event = event->next;
	// 		infector   = event->individual;

    //         contact_event* new_event = calloc( 1, sizeof( contact_event ) );
    //         new_event->day = day;
    //         new_event->source_id = infector->idx;
    //         new_event->contact_id = 2;
    //         new_event->network_id = 3;
    //         new_event->was_infected = FALSE; // We set this from Transmissions, later
    //         ++count;

    //         if (NULL == first) {
    //             first = new_event;
    //             last = new_event;
    //         } else {
    //             last->next = new_event;
    //             last = new_event;
    //         }

	// 		// t_infect = model->time - time_infected_infection_event( infector->infection_events );
	// 		// if( t_infect >= MAX_INFECTIOUS_PERIOD )
	// 		// 	continue;

    //         n_interaction = infector->n_interactions[ day ];
    //         if( n_interaction > 0 )
    //         {
    //             // interaction   = infector->interactions[ day ];

    //             // for( jdx = 0; jdx < n_interaction; jdx++ )
    //             // {
    //             //     // Create contact event
    //             //     contact_event* new_event = calloc( 1, sizeof( contact_event ) );
    //             //     new_event->day = day;
    //             //     new_event->source_id = infector->idx;
    //             //     new_event->contact_id = interaction->individual->idx;
    //             //     new_event->network_id = interaction->network_id;
    //             //     new_event->was_infected = FALSE; // We set this from Transmissions, later
    //             //     ++count;

    //             //     if (NULL == first) {
    //             //         first = new_event;
    //             //         last = new_event;
    //             //     } else {
    //             //         last->next = new_event;
    //             //         last = new_event;
    //             //     }
    //             //     interaction = interaction->next;
    //             // }
    //         }
    //     }
    // }

    // // Now loop over transmissions and change was_infected as required

	// individual *indiv;
	// infection_event *infection_event;
	// long pdx;
    // int found = 0;
    // int timeInfected;

    // contact_event* search_event = first;

	// for( pdx = 0; pdx < model->params->n_total; pdx++ )
	// {
	// 	indiv = &(model->population[pdx]);
	// 	infection_event = indiv->infection_events;

	// 	while(infection_event != NULL)
	// 	{
    //         search_event = first;
    //         found = 0;
    //         timeInfected = time_infected_infection_event( infection_event );
	// 		if( timeInfected != UNKNOWN )
	// 		{
    //             // find matching contact event to modify
    //             while ((0 == found) && NULL != search_event) {
    //                 if ( (search_event->source_id == infection_event->infector->idx) &&
    //                         (search_event->contact_id == indiv->idx) &&
    //                         (search_event->day == timeInfected) ) {
    //                     found = 1;
    //                     search_event->was_infected = TRUE;
    //                 }
    //                 search_event = search_event->next;
    //             }
    //         }
	// 		infection_event = infection_event->next;
    //     }
    // }

    last = model->contact_events;
    first = NULL;
    while (NULL != last) {
        if (last->day >= since) {
            if (NULL == first) {
                first = last;
            }
            ++count;
        }
        last = last->next;
    }

    contact_events_summary* summary = calloc(1,sizeof(contact_events_summary));
    summary->first = first;
    summary->count = count;

    return summary;
}