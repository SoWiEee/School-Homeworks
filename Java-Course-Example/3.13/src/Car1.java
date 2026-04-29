class Car1 {
	private String model;//設變數用private
	private String year;
	private double price;
	
	/* Set model, year, and price info of car. **///函式一律用public
	public void SetModel(String model) {//Set:用 public void Set名字(變數單位 變數名字)
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
	public String GetModel() {//Get用 public 變數單位 Get名字()
		return model;
	}
	public String GetYear() {
		return year;
	}
	public double GetPrice() {
		return price;
	}

	public static void main(String[] args) {
		/* Create two cars. **///2個CAR都是Class
		Car CarA = new Car();
		Car CarB = new Car();
		
		/* Set info to two cars. **/ 
		CarA.SetModel("BMW");//Set 用法: Class.Set函式( 內容 );
		CarA.SetYear("1995");
		CarA.SetPrice(20000);
		CarB.SetModel("BENZ");
		CarB.SetYear("2000");
		CarB.SetPrice(15000);
		
		/* Display info of cars. **///System.out.println裡頭用 Get!
		System.out.println("Car Sample A: " + CarA.GetModel() + " " + CarA.GetYear() + " $" + CarA.GetPrice());
		System.out.println("Car Sample B: " + CarB.GetModel() + " " + CarB.GetYear() + " $" + CarB.GetPrice());
		
		/* Discount cars' price. **/
		CarA.SetPrice(0.95 * CarA.GetPrice());//Set 用法: Class.Set函式( 內容 );
		CarB.SetPrice(0.93 * CarB.GetPrice());
		
		/* Display price of car again. **///System.out.println裡頭用 Get!
		System.out.println("Car Sample A price(5% off): " + CarA.GetPrice());
		System.out.println("Car Sample B price(7% off): " + CarB.GetPrice());
	}
}
