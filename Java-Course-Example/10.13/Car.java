public class Car implements CarbonFootprint {
	private double averageYearlyMiles;
	private double averageMPG;
	private final int kgCO2PerMile = 9;

	//constructor
	public Car(double miles, double MPG) {
		averageYearlyMiles = miles;
		averageMPG = MPG;
	}//end of constructor

	public void setAverageYearlyMiles(double miles) {
		averageYearlyMiles = miles;
	}

	public void setAverageMPG(double MPG) {
		averageMPG = MPG;
	}

	public double getAverageYearlyMiles() {
		return averageYearlyMiles;
	}

	public double getAverageMPG() {
		return averageMPG;
	}

	@Override
	public String toString() {
		return String.format("%s: %.2f \n%s: %.2f \n", "Average yearly miles is ", getAverageYearlyMiles(), "Average MPG is ", getAverageMPG());
	}

	@Override
	public double getCarbonFootprint() {
		return ((getAverageYearlyMiles() * getAverageMPG()) * kgCO2PerMile);
	}
}
