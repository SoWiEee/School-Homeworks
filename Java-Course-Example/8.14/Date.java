public class Date {
	private int month;
	private int day;
	private int year;
	private final String[] monthWords = { "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December" };
	private final int[] monthDays = { 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31 };

	public Date(int DDD, int YYYY) {
		setYear(YYYY);
		setDay(daysToMonth(DDD));
	}

	public Date(String MM, int DD, int YYYY) {
		setYear(YYYY);
		toMonthNumber(MM);
		setDay(DD);
	}

	public Date(int MM, int DD, int YYYY) {
		setYear(YYYY);
		setMonth(MM);
		setDay(DD);
	}

	public void setYear(int YYYY) {
		year = YYYY;
	}

	public void setMonth(int MM) {
		month = (MM >= 1 && MM <= 12) ? MM : 1;
	}

	public void setDay(int DD) {
		this.day = (DD >= 1 && DD <= monthDays[this.month - 1]) ? DD : 1;

		if (leapYear(this.year) && this.month == 2 && DD == 29)
			this.day = DD;
	}

	public boolean leapYear(int year) {
		return (year % 400 == 0 || (year % 4 == 0 && year % 100 != 0)) ? true : false;
	}

	private void toMonthNumber(String MM) {
		int i;
		for (i = 1; i <= 12; i++)
			if (MM.equals(monthWords[i - 1]))
				break;
		setMonth(i);
	}

	public int daysToMonth(int DDD) {
		int monthCount = 1;

		if (DDD < 1 || DDD > 366) {
			setMonth(1);
			return 1;
		}

		if (!leapYear(year))
			for (int i = 0; i < 12; i++) {
				if (DDD > monthDays[i])
					DDD -= monthDays[i];
				else
					break;
				monthCount++;
			}
		else
			for (int i = 0; i < 12; i++) {
				if (i != 1) {
					if (DDD > monthDays[i])
						DDD -= monthDays[i];
					else
						break;
					monthCount++;
				} else {
					if (DDD > 29)
						DDD -= 29;
					else
						break;
					monthCount++;
				}
			}
		setMonth(monthCount);
		return DDD;
	}

	private int monthsToDays() {
		int totalDays = 0;
		for (int i = 0; i < this.month - 1; i++)
			totalDays += monthDays[i];
		if (leapYear(this.year) && this.month > 2)
			totalDays++;
		return totalDays + this.day;
	}

	@Override
	public String toString() {
		return String.format("%d/%d/%d", this.month, this.day, this.year);
	}

	public String toString(int mode) {
		switch (mode) {
			case 1:
				return String.format("%d/%d/%d", this.month, this.day, this.year);
			case 2:
				return String.format("%s %d, %d", this.monthWords[this.month - 1], this.day, this.year);
			case 3:
				return String.format("%d %d", monthsToDays(), this.year);
			default:
				return String.format("%d/%d/%d", this.month, this.day, this.year);
		}
	}
}
