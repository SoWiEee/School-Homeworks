public class BasePlusCommissionEmployee extends CommissionEmployee {
	private double baseSalary;

	public BasePlusCommissionEmployee(String first, String last, String ssn, int month, int day, int year, double grossSales, double rate, double baseSalary) {
		super(first, last, ssn, month, day, year, grossSales, rate);
		setBaseSalary(baseSalary);
	}

	public void setBaseSalary(double salary) {
		baseSalary = salary < 0.0 ? 0.0 : salary;
	}

	public double getBaseSalary() {
		return baseSalary;
	}

	public double getPaymentAmount() {
		return getBaseSalary() + super.getPaymentAmount();
	}

	public String toString() {
		return "\nbase-salaried commission employee: " + super.getFirstName() + " " + super.getLastName() + "\nsocial security number: " + super.getSocialSecurityNumber() + "\nbirth date: " + super.getBirthDate().toDateString();
	}
}
