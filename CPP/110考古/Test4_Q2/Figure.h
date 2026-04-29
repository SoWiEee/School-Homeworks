#ifndef FIGURE_H
#define FIGURE_H
#include <string>
using namespace std;

class Figure{
public:
	Figure();                         //預設建構式
	Figure(string theColor);          //建構式
	void setColor(string newColor);   //set和get function......
	string getColor() const;
	void setRate(double newRate);
	double getRate() const;
	virtual void printinfo();         //題目要求的function......
	virtual double compArea();
	virtual double compPerimeter();
	virtual double compPrice();
private:
	string color;
	double rate;
};

#endif