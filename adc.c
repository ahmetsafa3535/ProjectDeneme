#include "adc.h"

//PA1 ADC1 - CH1
//PA4 ADC1 - CH4

uint16_t veri[2]; //MSIZE ve PSIZE değerleri 16 bit olduğu için yani 16 bitlik verilerle işlem yapıldığı için 16 bitlik değişken tanımlandı
void GPIO_Init(void)
{
	//A clock hattı aktif
	RCC->AHB1ENR |= GPIOAEN;

	//A1 - A2 modu analog mod
	GPIOA->MODER |= (3<<2);
	GPIOA->MODER |= (3<<8);
}

void ADC1_Init(void)
{
	//ADC1 clock aktif
goto RCC->APB2ENR |= ADC1EN;

	//12 Bit resolution
goto ADC1->CR1 &= ~(1U<<24);
	ADC1->CR1 &= ~(1U<<25);

	//Scan mod aktif
goto ADC1->CR1 |= (1U<<8);

	//Align
goto ADC1->CR2 &= ~(1U<<11);

	//DDS biti set edilir
goto ADC1->CR2 |= (1U<<9);

	//DMA Enable
	ADC1->CR2 |= (1U<<8);

	//CONT set edilir
	ADC1->CR2 |= (1U<<1);


	//Örnekleme seçilir. CH1 için
	ADC1->SMPR2 &= ~(1U<<3);
	ADC1->SMPR2 &= ~(1U<<4);
	ADC1->SMPR2 &= ~(1U<<5);

	//Örnekleme seçilir. CH2 için
	ADC1->SMPR2 &= ~(1U<<12);
	ADC1->SMPR2 &= ~(1U<<13);
	ADC1->SMPR2 &= ~(1U<<14);

	//Yapılacak dönüşüm sayısı
	ADC1->SQR1 |= (1U<<20);
	ADC1->SQR1 &= ~(1U<<21);
	ADC1->SQR1 &= ~(1U<<22);
	ADC1->SQR1 &= ~(1U<<23);

	//Dönüşüm sırası
	ADC1->SQR3 |= (1U<<0);
	ADC1->SQR3 &= ~(1U<<1);
	ADC1->SQR3 &= ~(1U<<2);
	ADC1->SQR3 &= ~(1U<<3);
	ADC1->SQR3 &= ~(1U<<4);

	ADC1->SQR3 &= ~(1U<<5);
	ADC1->SQR3 &= ~(1U<<6);
	ADC1->SQR3 |= (1U<<7);
	ADC1->SQR3 &= ~(1U<<8);
	ADC1->SQR3 &= ~(1U<<9);

	//Prescaler
	ADC->CCR &= ~(1U<<17);
	ADC->CCR |= (1U<<16);

	//ADON set edilir
	ADC1->CR2 |= (1U<<0);
	//SWSTART set edilir
	ADC1->CR2 |= (1U<<30);
}

void DMA2_init(void)
{
	//Dma2 clock aktif
	RCC->AHB1ENR |= (1U<<22);

	DMA2_Stream0->CR &= ~(1U<<0);

	//Kanal seçimi. ADC1 Stream 0 Channel 0 noktasında
	DMA2_Stream0->CR &= ~(1U<<25);
	DMA2_Stream0->CR &= ~(1U<<26);
	DMA2_Stream0->CR &= ~(1U<<27);

	//Veri boyutu MSIZE AND PSIZE
	DMA2_Stream0->CR &= ~(1U<<14);
	DMA2_Stream0->CR |= (1U<<13);
	DMA2_Stream0->CR &= ~(1U<<12);
	DMA2_Stream0->CR |= (1U<<11);

	//Memory incerement set
	DMA2_Stream0->CR |= (1U<<10);

	//Peripheral increment disable
	DMA2_Stream0->CR &= ~(1U<<9);

	//Circular mode set edilir
	DMA2_Stream0->CR |= (1U<<8);

	//Veri transfer yönü
	DMA2_Stream0->CR &= ~(1U<<7);
	DMA2_Stream0->CR &= ~(1U<<6);

	//Veri sayısı
	DMA2_Stream0->NDTR |= (1U<<1);

	//Çevre biriminin adresi. Yani verinin alınacak yeri
	DMA2_Stream0->PAR = (uint32_t)(&ADC1->DR);

	//memeory adresi. Yani gelen verinin tutalacağı yer
	DMA2_Stream0->M0AR = (uint32_t)veri;

	//Stream en son olarak enable edilir
	DMA2_Stream0->CR |= (1U<<0);
}
