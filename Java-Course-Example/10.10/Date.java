public class Date {
	private int month;
	private int day;
	private int year;

	public Date(int month, int day, int year) {
		this.month = checkMonth(month);
		this.year = year;
		this.day = checkDay(day);
	}

	private int checkMonth(int month) {
		if (month > 0 && month <= 12)
			return month;
		else
			return 1;
	}

	private int checkDay(int day) {
		int daysPerMonth[] = { 0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31 };

		if (day > 0 && day <= daysPerMonth[month])
			return day;
		if (month == 2 && day == 29 && (year % 400 == 0 || (year % 4 == 0 && year % 100 != 0)))
			return day;
		return 1;
	}

	public int getMonth() {
		return month;
	}

	public String toDateString() {
		return month + "/" + day + "/" + year;
	}
}
