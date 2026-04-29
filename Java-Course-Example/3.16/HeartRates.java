package javaHw;

public class HeartRates {
	private String first_name;
	private String last_name;
	private int month, day, year;
	
	public HeartRates() {
		this.first_name = "none";
		this.last_name ="none";
		this.month = 0;
		this.day = 0;
		this.year = 0;
	}
	
	public HeartRates(String first_name, String last_name, int month, int day, int year) {
		this.first_name = first_name;
		this.last_name = last_name;
		this.month = month;
		this.day = day;
		this.year = year;
	}
	
	public void setFirstName(String first_name) {
		this.first_name = first_name;
	}
	public String getFirstName() {
		return this.first_name;
	}
	
	public void setLastName(String last_name) {
		this.last_name = last_name;
	}
	public String getLastName() {
		return this.last_name;
	}
	
	public void setMonth(int month) {
		this.month = month;
	}
	public int getMonth() {
		return this.month;
	}
	
	public void setDay(int day) {
		this.day = day;
	}
	public int getDay() {
		return this.day;
	}
	
	public void setYear(int year) {
		this.year = year;
	}
	public int getYear() {
		return this.year;
	}
	
	public int getAge(int currentMonth, int currentDay, int currentYear) {
		int age = currentYear - this.year;
		
		if (this.month > currentMonth)
			if (this.day > currentDay)
				age--;
			
		return age;
	}
	
	public int maxHeartRate(int age) {
		return 220 - age;
	}
	
	public String targetHeartRate(int maxHeartRate) {
		String thr = String.format("%.2f~%.2f", maxHeartRate * .5, maxHeartRate * .85);
		return thr;
	}
}
