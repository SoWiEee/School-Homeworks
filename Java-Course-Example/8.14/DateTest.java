public class DateTest {
	public static void main(String[] args) {
		Date date1 = new Date(3, 2, 2000);

		System.out.printf("%s\n", date1.toString(1));
		System.out.printf("%s\n", date1.toString(2));
		System.out.printf("%s\n", date1.toString(3));
	}
}
