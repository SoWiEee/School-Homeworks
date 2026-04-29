public class SalariedEmployee extends Employee {
	private double weeklySalary;

	public SalariedEmployee(String first, String last, String ssn, int month, int day, int year, double salary) {
		super(first, last, ssn, month, day, year);
		setWeeklySalary(salary);
	}

	public void setWeeklySalary(double salary) {
		weeklySalary = salary < 0.0 ? 0.0 : salary;
	}

	public double getWeeklySalary() {
		return weeklySalary;
	}

	@Override
	public double earnings() {
		return getWeeklySalary();
	}

	public String toString() {
		return "\nsalaried employee: " + super.toString();
	}
}
