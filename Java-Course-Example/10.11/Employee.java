public abstract class Employee implements Payable {
	private String firstName;
	private String lastName;
	private String socialSecurityNumber;
	private Date birthDate;

	public Employee(String firstNmae, String lastName, String ssn, int month, int day, int year) {
		this.firstName = firstNmae;
		this.lastName = lastName;
		this.socialSecurityNumber = ssn;
		this.birthDate = new Date(month, day, year);
	}

	public void setFirstName(String firstName) {
		this.firstName = firstName;
	}

	public String getFirstName() {
		return firstName;
	}

	public void setLastName(String lastName) {
		this.lastName = lastName;
	}

	public String getLastName() {
		return lastName;
	}

	public void setSocialSecurityNumber(String ssn) {
		this.socialSecurityNumber = ssn;
	}

	public String getSocialSecurityNumber() {
		return socialSecurityNumber;
	}

	public void setBirthDate(int month, int day, int year) {
		this.birthDate = new Date(month, day, year);
	}

	public Date getBirthDate() {
		return birthDate;
	}

	public String toString() {
		return getFirstName() + " " + getLastName() + "\nsocial security number: " + getSocialSecurityNumber() + "\nBirthdate: " + birthDate.toDateString();
	}
}
