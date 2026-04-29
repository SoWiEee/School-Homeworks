package javaHw;
import java.util.*;

public class HeartRateClassTest {
	public static void main(String[] args) {
		HeartRates person1 = new HeartRates();
		Scanner jin = new Scanner(System.in);
		int cMonth = new Date().getMonth() + 1;
		int cDay = new Date().getDate();
		int cYear = new Date().getYear() + 1900;

		System.out.print("Enter your first name: ");
		person1.setFirstName(jin.nextLine());
		System.out.print("Enter your last name: ");
		person1.setLastName(jin.nextLine());
		System.out.print("Enter your birth(mm dd yy): ");
		person1.setMonth(jin.nextInt());
		person1.setDay(jin.nextInt());
		person1.setYear(jin.nextInt());

		int age = person1.getAge(cMonth, cDay, cYear);
		System.out.printf("Name: %s, %s\n", person1.getFirstName(), person1.getLastName());
		System.out.printf("Birth(mm-dd-yy): %d-%d-%d\n", person1.getMonth(), person1.getDay(), person1.getYear());
		System.out.printf("Age: %d\n", age);
		System.out.printf("Maximum Heart Rate: %d\n", person1.maxHeartRate(age));
		System.out.printf("Target Heart Rate Range: %s\n", person1.targetHeartRate(person1.maxHeartRate(age)));
		jin.close();
	}
}
