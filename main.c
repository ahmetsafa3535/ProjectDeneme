/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.c
  * @brief          : Main program body
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2024 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* USER CODE END Header */
/* Includes ------------------------------------------------------------------*/
#include "main.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include "math.h"
/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */

/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */
/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/
I2C_HandleTypeDef hi2c1;

/* USER CODE BEGIN PV */

/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
static void MX_GPIO_Init(void);
static void MX_I2C1_Init(void);
/* USER CODE BEGIN PFP */

/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */
#define BMP180ADDRES	0x77<<1
float AC1,AC2,AC2,AC3,AC4,AC5,AC6,B1,B2,MB,MC,MD;
long X1, X2, X3,p,B3,B5,B6,T;
unsigned long B4,B7;
void readCalibdata(void) //read_cLLİVERATİON_DATA
{
	uint16_t calib0 = 0xAA;
	uint8_t rxdata[22]; //AC katsayıları 2 byte olduğu için
	HAL_I2C_Mem_Read(&hi2c1, BMP180ADDRES, calib0, 1, rxdata, 22, 100);
	AC1 = ((rxdata[0] << 8) | rxdata[1]);
	AC2 = ((rxdata[2] << 8) | rxdata[3]);
	AC3 = ((rxdata[4] << 8) | rxdata[5]);
	AC4 = ((rxdata[6] << 8) | rxdata[7]);
	AC5 = ((rxdata[8] << 8) | rxdata[9]);
	AC6 = ((rxdata[10] << 8) | rxdata[11]);
	B1 = ((rxdata[12] << 8) | rxdata[13]);
	B2 = ((rxdata[14] << 8) | rxdata[15]);
	MB = ((rxdata[16] << 8) | rxdata[17]);
	MC = ((rxdata[18] << 8) | rxdata[19]);
	MD = ((rxdata[20] << 8) | rxdata[21]);
}

float uncomp_tem(void) //get_utemp
{
	uint16_t ut;
	uint8_t rxdata[2];
	HAL_I2C_Mem_Write(&hi2c1, BMP180ADDRES, 0xF4, 1, 0x2E, 1, 100);
	HAL_Delay(5);
	HAL_I2C_Mem_Read(&hi2c1, BMP180ADDRES, 0XF6, 1, rxdata, 2, 100); //Burada register adres boyutu 1 byte yani ierçsinde 1 byte veri tutar.
	ut = ((rxdata[0] << 8) + rxdata[1]);
	return ut;
}

float uncom_pressure(uint8_t oss) //get_upress
{
	uint8_t gelendata[3];
	uint8_t data[1] = 0x34;
	uint32_t up;
	HAL_I2C_Mem_Write(&hi2c1, BMP180ADDRES, 0xF4, 1, data[0]+(oss<<6), 1, 100);
	switch (oss) {
		case 0:
			HAL_Delay(5);
			break;

		case 1:
			HAL_Delay(8);
			break;

		case 2:
				HAL_Delay(15);
				break;

		case 3:
			HAL_Delay(26);
		default:
			break;
	}
	HAL_I2C_Mem_Read(&hi2c1, BMP180ADDRES, 0xF6, 1, gelendata, 3, 100);
	up = ((gelendata[0] << 16) + (gelendata[1] << 8) + (gelendata[2]));
	return up;
}

void reel_temp(void) //bmp180_gettemp
{
	float donenut = uncomp_tem();
	X1 = (donenut - AC6) * AC5 / pow(2,15);
	X2 = MC * pow(2,11) / (X1 + MD);
	T = (B5 + 8) / pow(2,4);
}

void son_temp(void)
{
	B6 = B5 - 4000;
	X1 (B2 * (B6 * B6 / pow(2,12))) / pow(2,11);
	X2 = AC2 * B6 / pow(2,11);
	X3 = X1 + X2;
	B3 = (((AC1*4+X3) << oss) + 2) / 4;
	X1 = AC3 * B6 / pow(2,13);
	X2 = (B1 * (B6 * B6 / pow(2,12) / pow(2,16)));
	X3 = ((X1 + X2) + 2)/ pow(2,2);

}

/* USER CODE END 0 */

/**
  * @brief  The application entry point.
  * @retval int
  */
int main(void)
{
  /* USER CODE BEGIN 1 */

  /* USER CODE END 1 */

  /* MCU Configuration--------------------------------------------------------*/

  /* Reset of all peripherals, Initializes the Flash interface and the Systick. */
  HAL_Init();

  /* USER CODE BEGIN Init */

  /* USER CODE END Init */

  /* Configure the system clock */
  SystemClock_Config();

  /* USER CODE BEGIN SysInit */

  /* USER CODE END SysInit */

  /* Initialize all configured peripherals */
  MX_GPIO_Init();
  MX_I2C1_Init();
  /* USER CODE BEGIN 2 */

  /* USER CODE END 2 */

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
  while (1)
  {
    /* USER CODE END WHILE */

    /* USER CODE BEGIN 3 */
	  readCalibdata();
	  uncomp_tem();
  }
  /* USER CODE END 3 */
}

/**
  * @brief System Clock Configuration
  * @retval None
  */
void SystemClock_Config(void)
{
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};

  /** Configure the main internal regulator output voltage
  */
  __HAL_RCC_PWR_CLK_ENABLE();
  __HAL_PWR_VOLTAGESCALING_CONFIG(PWR_REGULATOR_VOLTAGE_SCALE1);
  /** Initializes the RCC Oscillators according to the specified parameters
  * in the RCC_OscInitTypeDef structure.
  */
  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSI;
  RCC_OscInitStruct.HSIState = RCC_HSI_ON;
  RCC_OscInitStruct.HSICalibrationValue = RCC_HSICALIBRATION_DEFAULT;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_NONE;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  {
    Error_Handler();
  }
  /** Initializes the CPU, AHB and APB buses clocks
  */
  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK
                              |RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2;
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_HSI;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV1;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_0) != HAL_OK)
  {
    Error_Handler();
  }
}

/**
  * @brief I2C1 Initialization Function
  * @param None
  * @retval None
  */
static void MX_I2C1_Init(void)
{

  /* USER CODE BEGIN I2C1_Init 0 */

  /* USER CODE END I2C1_Init 0 */

  /* USER CODE BEGIN I2C1_Init 1 */

  /* USER CODE END I2C1_Init 1 */
  hi2c1.Instance = I2C1;
  hi2c1.Init.ClockSpeed = 100000;
  hi2c1.Init.DutyCycle = I2C_DUTYCYCLE_2;
  hi2c1.Init.OwnAddress1 = 0;
  hi2c1.Init.AddressingMode = I2C_ADDRESSINGMODE_7BIT;
  hi2c1.Init.DualAddressMode = I2C_DUALADDRESS_DISABLE;
  hi2c1.Init.OwnAddress2 = 0;
  hi2c1.Init.GeneralCallMode = I2C_GENERALCALL_DISABLE;
  hi2c1.Init.NoStretchMode = I2C_NOSTRETCH_DISABLE;
  if (HAL_I2C_Init(&hi2c1) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN I2C1_Init 2 */

  /* USER CODE END I2C1_Init 2 */

}

/**
  * @brief GPIO Initialization Function
  * @param None
  * @retval None
  */
static void MX_GPIO_Init(void)
{

  /* GPIO Ports Clock Enable */
  __HAL_RCC_GPIOH_CLK_ENABLE();
  __HAL_RCC_GPIOA_CLK_ENABLE();
  __HAL_RCC_GPIOB_CLK_ENABLE();

}

/* USER CODE BEGIN 4 */

/* USER CODE END 4 */

/**
  * @brief  This function is executed in case of error occurrence.
  * @retval None
  */
void Error_Handler(void)
{
  /* USER CODE BEGIN Error_Handler_Debug */
  /* User can add his own implementation to report the HAL error return state */
  __disable_irq();
  while (1)
  {
  }
  /* USER CODE END Error_Handler_Debug */
}

#ifdef  USE_FULL_ASSERT
/**
  * @brief  Reports the name of the source file and the source line number
  *         where the assert_param error has occurred.
  * @param  file: pointer to the source file name
  * @param  line: assert_param error line source number
  * @retval None
  */
void assert_failed(uint8_t *file, uint32_t line)
{
  /* USER CODE BEGIN 6 */
  /* User can add his own implementation to report the file name and line number,
     ex: printf("Wrong parameters value: file %s on line %d\r\n", file, line) */
  /* USER CODE END 6 */
}
#endif /* USE_FULL_ASSERT */

