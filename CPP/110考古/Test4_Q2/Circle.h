#ifndef CIRCLE_H
#define CIRCLE_H
#include "Figure.h"
#include "Point.h"
#include <string>
using namespace std;

class Circle : public Figure{
public:
	Circle();                                                    //預設建構式
	Circle(string theColor, double theRadius, Point theCenter);  //建構式
	void setRadius(double newRadius);                            //set和get function......
	double getRadius() const;
	void setCenter(Point newCenter);
	Point getCenter() const;
	string getClass() const;
	virtual void printinfo();                                    //題目要求的function......
	virtual double compArea();
	virtual double compPerimeter();
	virtual double compPrice(); 
private:
	double radius;
	Point center;
};

#endif