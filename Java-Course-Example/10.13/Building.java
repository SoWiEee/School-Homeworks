public class Building implements CarbonFootprint {
	private double averageMonthlyKwh;
	private final int months = 12;

	//private double carbonFootprint;
	//constructor
	public Building(double monthlyConsumption) {
		averageMonthlyKwh = monthlyConsumption;
	}//end of constructor

	public void setAverageMonthlyKwh(double monthlyConsumption) {
		averageMonthlyKwh = monthlyConsumption;
	}

	public double getAverageMonthlyKwh() {
		return averageMonthlyKwh;
	}

	@Override
	public String toString() {
		return String.format("%s: %.2f\n", "the monthly consumption is ", getAverageMonthlyKwh());
	}

	@Override
	public double getCarbonFootprint() {
		return getAverageMonthlyKwh() * months;
	}
}
