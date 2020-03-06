/*
 * constant.h
 *
 *  Created on: 5 Mar 2020
 *      Author: hinchr
 */

#ifndef CONSTANT_H_
#define CONSTANT_H_

enum DISEASE_STATUS{
	UNINFECTED,
	PRESYMPTOMATIC,
	SYMPTOMATIC,
	RECOVERED
};

#define MAX_DAILY_INTERACTIONS_KEPT 5
#define MAX_TIME 1000
#define MAX_INFECTIOUS_PERIOD 40

gsl_rng * rng;

#endif /* CONSTANT_H_ */

