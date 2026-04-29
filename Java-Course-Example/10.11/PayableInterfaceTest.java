public class PayableInterfaceTest {
	public static void main(String[] args) {
		Payable[] payableObjects = new Payable[6];

		System.out.println("Invoices and Employees processed polymorphically:\n");

		payableObjects[0] = new Invoice("01234", "seat", 2, 375.00);
		payableObjects[1] = new Invoice("56789", "tire", 4, 79.95);
		payableObjects[2] = new SalariedEmployee("John", "Smith", "111-11-1111", 6, 15, 1944, 800.00);
		payableObjects[3] = new CommissionEmployee("Sue", "Jones", "222-22-2222", 9, 8, 1954, 10000, .06);
		payableObjects[4] = new BasePlusCommissionEmployee("Bob", "Lewis", "333-33-3333", 3, 2, 1965, 5000, .04, 300);
		payableObjects[5] = new HourlyEmployee("Karen", "Price", "444-44-4444", 12, 29, 1960, 16.75, 40);

		for (Payable currentPayable : payableObjects) {
			System.out.printf("%s \n%s: ", currentPayable.toString(), "payment due");

			if (currentPayable instanceof BasePlusCommissionEmployee) {
				BasePlusCommissionEmployee currentEmployee = (BasePlusCommissionEmployee) currentPayable;

				double oldBaseSalary = currentEmployee.getBaseSalary();
				currentEmployee.setBaseSalary(oldBaseSalary * (1.1));
				System.out.printf("$%,.2f\n\n", currentEmployee.getPaymentAmount());
			} else {
				System.out.printf("$%,.2f\n\n", currentPayable.getPaymentAmount());
			}
		}
	}
}
