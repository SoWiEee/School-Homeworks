public class CommissionEmployee extends Employee {
	private double grossSales;
	private double commissionRate;

	public CommissionEmployee(String first, String last, String ssn, int month, int day, int year, double grossSales, double commissionRate) {
		super(first, last, ssn, month, day, year);
		setGrossSales(grossSales);
		setCommissionRate(commissionRate);
	}

	public void setCommissionRate(double rate) {
		commissionRate = (rate > 0.0 && rate < 1.0) ? rate : 0.0;
	}

	public double getCommissionRate() {
		return commissionRate;
	}

	public void setGrossSales(double sales) {
		grossSales = sales < 0.0 ? 0.0 : sales;
	}

	public double getGrossSales() {
		return grossSales;
	}

	public double getPaymentAmount() {
		return getCommissionRate() * getGrossSales();
	}

	public String toString() {
		return "\ncommission employee: " + super.toString();
	}
}
