import java.io.IOException;

class ExceptionA extends Exception {
}

class ExceptionB extends ExceptionA {
}

public class Demo2 {
	public static void main(String[] args) {
		try {
			throw new ExceptionA();
		} catch (Exception exception) {
			System.err.println(exception.toString());
		}

		try {
			throw new ExceptionB();
		} catch (Exception exception) {
			System.err.println(exception.toString());
		}

		try {
			throw new NullPointerException();
		} catch (Exception exception) {
			System.err.println(exception.toString());
		}

		try {
			throw new IOException();
		} catch (Exception exception) {
			System.err.println(exception.toString());
		}
	}
}
