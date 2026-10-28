
#ifndef INC_LOWCONSUME_H_
	#define INC_LOWCONSUME_H_

	#include "globalVariables.h"

	#ifdef UCAN_LOW_CONSUME_PINS //loose fysetc ucan boards 28/10/2026 - PA4 has no pad on the ucan: the reset line towards the RES pads of C2 and BH leaves from the DO pad (PA13, SWDIO), as in GiUCAN
		#define CHIP_LOW_CONSUME_Pin GPIO_PIN_13
	#else
		#define CHIP_LOW_CONSUME_Pin GPIO_PIN_4
	#endif
	#define CHIP_LOW_CONSUME_Port GPIOA
	#define CHIP_LOW_CONSUME CHIP_LOW_CONSUME_Port , CHIP_LOW_CONSUME_Pin

	#define CAN_LOW_CONSUME_Pin GPIO_PIN_5
	#define CAN_LOW_CONSUME_Port GPIOA
	#define CAN_LOW_CONSUME CAN_LOW_CONSUME_Port , CAN_LOW_CONSUME_Pin

	#define CHIP_RESET_DURATION 500 //time in milliseconds

	void lowConsume_init(void);
	void Reset_Other_Chips(void);
	void Remove_Reset_From_Other_Chips(void);
	void CAN_LOW_CONSUME_On(void);
	void CAN_LOW_CONSUME_Off(void);
	void lowConsume_process(void);
	void reduceConsumption(void);
	void wakeUpAllProcessorsAndTransceivers(void);

#endif /* INC_LOWCONSUME_H_ */
