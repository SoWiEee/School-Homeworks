import java.text.DecimalFormat;

import javax.swing.JOptionPane;

public class PayrollSystemTest {
	public static void main(String[] args) {
		DecimalFormat twoDigits = new DecimalFormat("0.00");

		Employee employees[] = new Employee[4];

		employees[0] = new SalariedEmployee("John", "Smith", "111-11-1111", 6, 15, 1944, 800.00);
		employees[1] = new CommissionEmployee("Sue", "Jones", "222-22-2222", 9, 8, 1954, 10000, .06);
		employees[2] = new BasePlusCommissionEmployee("Bob", "Lewis", "333-33-3333", 3, 2, 1965, 5000, .04, 300);
		employees[3] = new HourlyEmployee("Karen", "Price", "444-44-4444", 12, 29, 1960, 16.75, 40);

		String output = "";
		int currentMonth = Integer.parseInt(JOptionPane.showInputDialog("Current month: "));

		while (!(currentMonth >= 0 && currentMonth <= 12)) {
			currentMonth = Integer.parseInt(JOptionPane.showInputDialog("Current month: "));
		}

		for (int i = 0; i < employees.length; i++) {
			output += employees[i].toString();

			if (employees[i] instanceof BasePlusCommissionEmployee) {
				BasePlusCommissionEmployee currentEmployee = (BasePlusCommissionEmployee) employees[i];

				double oldBaseSalary = currentEmployee.getBaseSalary();
				output += "\nnew base salary with 10% increase is : $" + currentEmployee.getBaseSalary();
			}

			if (currentMonth == employees[i].getBirthDate().getMonth())
				output += "\nearned $" + employees[i].earnings() + " plus $100.00 birthday bonus\n";
			else
				output += "\nearned $" + employees[i].earnings() + "\n";
		}

		for (int j = 0; j < employees.length; j++)
			output += "\nEmployee " + j + " is a " + employees[j].getClass().getName();
		JOptionPane.showMessageDialog(null, output);
		System.exit(0);
	}
}
