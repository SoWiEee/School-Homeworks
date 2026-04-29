
public class Car {
	/* Model, Year, and price of Car class. **/
	private String model;
	private String year;
	private double price;
	
	/* Constructor to initialize model, year, and price. **/
	public Car() {
		model = null;
		year = null;
		price = 0;
	}
	
	/* Set model, year, and price info of car. **/
	public void SetModel(String model) {
		this.model = model;
	}
	public void SetYear(String year) {
		this.year = year;
	}
	public void SetPrice(double price) {
		if (price >= 0) { /* Determine whether the input is valid or not. **/
			this.price = price; /* Set valid value to price. **/
		}
	}
	
	/* Get model, year, and price info. **/ 
	public String GetModel() {
		return model;
	}
	public String GetYear() {
		return year;
	}
	public double GetPrice() {
		return price;
	}
	
	/* Create two sample car class to demonstrate Car class capabilities. **/
	public void CarApplication() {
		
		/* Create two cars. **/
		Car CarA = new Car();
		Car CarB = new Car();
		
		/* Set info to two cars. **/ 
		CarA.SetModel("BMW");
		CarA.SetYear("1995");
		CarA.SetPrice(20000);
		CarB.SetModel("BENZ");
		CarB.SetYear("2000");
		CarB.SetPrice(15000);
		
		/* Display info of cars. **/
		System.out.println("Car Sample A: " + CarA.GetModel() + " " + CarA.GetYear() + " $" + CarA.GetPrice());
		System.out.println("Car Sample B: " + CarB.GetModel() + " " + CarB.GetYear() + " $" + CarB.GetPrice());
		
		/* Discount cars' price. **/
		CarA.SetPrice(0.95 * CarA.GetPrice());
		CarB.SetPrice(0.93 * CarB.GetPrice());
		
		/* Display price of car again. **/
		System.out.println("Car Sample A price(5% off): " + CarA.GetPrice());
		System.out.println("Car Sample B price(7% off): " + CarB.GetPrice());
	}

}
