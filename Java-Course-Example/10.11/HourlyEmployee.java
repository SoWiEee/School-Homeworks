public class HourlyEmployee extends Employee {
	private double wage;
	private double hours;

	public HourlyEmployee(String first, String last, String ssn, int month, int day, int year, double wage, double hours) {
		super(first, last, ssn, month, day, year);
		setWage(wage);
		setHours(hours);
	}

	public void setWage(double wage) {
		this.wage = wage < 0.0 ? 0.0 : wage;
	}

	public double getWage() {
		return wage;
	}

	public void setHours(double hours) {
		this.hours = (hours >= 0.0 && hours <= 168.0) ? hours : 0.0;
	}

	public double getHours() {
		return hours;
	}

	public double getPaymentAmount() {
		if (hours <= 40)
			return wage * hours;
		else
			return 40 * wage + (hours - 40) * wage * 1.5;
	}

	public String toString() {
		return "\nhourly employee: " + super.toString();
	}
}
