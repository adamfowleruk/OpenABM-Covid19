/*
 * contact_event.h
 *
 *  Created on: 7 Dec 2022
 *      Author: Adam Fowler <adam@adamfowler.org> <adam.fowler@spc.ox.ac.uk>
 * Description: Defines a contact event between two people. Is an instantiation of an interaction on a particular day
 */

#ifndef CONTACT_EVENT_H_
#define CONTACT_EVENT_H_

/************************************************************************/
/******************************* Includes *******************************/
/************************************************************************/

#include "structure.h"
#include "model.h"

/************************************************************************/
/****************************** Structures  *****************************/
/************************************************************************/

struct contact_event{
    // The following three are common for all contact events
    long source_id;
    long contact_id;
    long day;

    // TODO add strain to this contact event for multi-strain/disease evaluations

    // These are INTERNAL model risk evaluations, and not intervention risk evaluation levels
    double risk_threshold; // threshold (current hazard budget) for infection comparison
    double risk_evaluation;
    // Note if risk_evaluation > risk_threshold then was_infected will be true

    // The INTERNAL model original hazard (susceptibility) of the individual at the start of the simulation
    double susceptibility;

    // The following are reportable components of the above risk_evaluation value
    // The following are only set for a duration risk evaluation model
    double duration_minutes;

    // The following are only set if this contact event resulted in a transmission
    int was_infected;
    short network_id;

    contact_event* next;
};

struct contact_events_summary{
    long count;
    contact_event* first;
};

/************************************************************************/
/******************************  Functions  *****************************/
/************************************************************************/

contact_events_summary* get_contact_events( model*, int );

#endif /* CONTACT_EVENT_H_ */
