
public class Clock {
	/* Hour, minute, and second data of clock.**/
	private int hour;//提供一個構造函數來初始化三個實例變量並假定提供的值是正確的。
	private int minute;
	private int second;
	/* Constructor to initialize hour, minute, and second.**/
	Clock(){
		hour = 0;
		minute = 0;
		second = 0;
	}
	/* Set hour**///為每個實例變量提供一個 SET方法。
	public void SetHour(int hour) {
		if(hour < 0 || hour > 23) { /* out of range 0~23**/
			this.hour = 0;//如果 HOUR 的值大於 23，則 SET 方法應將所有三個變量的值設置為 0。
		}
		else { 
			this.hour = hour;
		}
	}
	/* Set minute**///為每個實例變量提供一個 SET方法。
	public void SetMinute(int minute) {
		if(minute < 0 || minute > 59) { /* out of range 0~59**/
			this.minute = 0;//如果Minute的值大於 59，則 SET 方法應將所有三個變量的值設置為 0。
		}
		else {
			this.minute = minute;
		}
	}
	/* Set second**///為每個實例變量提供一個 SET方法。
	public void SetSecond(int second) {
		if(second < 0 || second > 59) { /* out of range 0~59**/
			this.second = 0;//如果Second的值大於 59，則 SET 方法應將所有三個變量的值設置為 0。
		}
		else {
			this.second = second;
		}
	}
	/* Display set time.**///提供以“hh:mm:ss”格式顯示時間的方法 DISPLAYTIME。
	public void DisplayTime() {//為每個實例變量提供一個 GET 方法。
		System.out.println(hour + ":" + minute + ":" + second);
	}

}
