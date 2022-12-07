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

contact_events_summary* get_contact_events( model* );

#endif /* CONTACT_EVENT_H_ */
