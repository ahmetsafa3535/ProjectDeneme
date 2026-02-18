#include "uart.h"
#include "stm32f407xx.h"
""""""""""""""""""""""""""""""""""""""""""""""""
	DENEME 1
	DENEME 2

//PA2 TX-------PA3 RX

void LED_init(void)
{
	//D clock aktif
	RCC->AHB1ENR |= GPIODEN;

	//Moder türü output
	GPIOD->MODER |= (1U<<24);
	GPIOD->MODER &= ~(1U<<25);
	GPIOD->MODER |= (1U<<26);
	GPIOD->MODER &= ~(1U<<27);
	GPIOD->MODER |= (1U<<28);
	GPIOD->MODER &= ~(1U<<29);
	GPIOD->MODER |= (1U<<30);
	GPIOD->MODER &= ~(1U<<31);
}

void GPIOA_init(void)
{
	//A clock aktif
	RCC->AHB1ENR |= GPIOAEN;

	//A2-A3 Alternatif fonksiyon
	GPIOA->MODER |= (1U<<5);
	GPIOA->MODER &= ~(1U<<4);
	GPIOA->MODER |= (1U<<7);
	GPIOA->MODER &= ~(1U<<6);

	//Alternate fonksiyon olarak AF7 seçildi
	GPIOA->AFR[0] |= (7U<<8);
	GPIOA->AFR[0] |= (7U<<12);
}

void USART2_init(void)
{
	//USART2 clock aktif
	RCC->APB1ENR |= USART2EN;

	//USART2 Aktif
	USART2->CR1 |= CR1_UE;

	//Kelime uzunluğu M bit-8Bit
	USART2->CR1 &= ~CR1_M;

	//1 Stop Bit
	USART2->CR2 &= ~(1U<<12);
	USART2->CR2 &= ~(1U<<13);

	//Baudrate 9600
	USART2->BRR = 0x683;

	//Transmitter ve Receiver aktif
	USART2->CR1 |= CR1_TE;
	USART2->CR1 |= CR1_RE;

	//Receiver Interrupt aktif
	USART2->CR1 |= CR1_RXNEIE;

	//USART2, NVIC hattı aktif
	NVIC_EnableIRQ(USART2_IRQn);

	//USART2, interrupt önceliği
	NVIC_SetPriority(USART2_IRQn,0);
}

void write_data(uint8_t ch)
{
	//Transmit Data Register boş mu diye bakılır. Set ise Data shift registera kayar ve başka veri yazılabilir.
	//O yüzden set olması beklenirki başka veri yazılabilsin.
	while(!(USART2->SR & (SR_TXE)));

	//TXE flag set ise yani veriler shift registera geçtiyse veriler yazılır
	USART2->DR = ch;
}

uint8_t receive_data(void)
{
	uint8_t temp;
	//Veri alındığında shift registera gelen veri TDR'a geçtiğinde RXNE flag set olur. Yani shift register
	//boş, başka verinin gelebileceğini söyler.O yüzden set olması beklenir
	while(!(USART2->SR & SR_RXNE));

	//Gelen veri alınır
	temp = USART2->DR;
	return temp;
}



