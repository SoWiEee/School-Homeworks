class ExceptionA extends Exception {
}

class ExceptionB extends ExceptionA {
}

class ExceptionC extends ExceptionB {
}

public class Demo {
	public static void main(String[] args) {
		try {
			throw new ExceptionC();
		} catch (ExceptionA exceptoin) {
			System.err.println("First Exception subclass caught. \n");
		}

		try {
			throw new ExceptionB();
		} catch (ExceptionA exception2) {
			System.out.println("Second Exception subclass caught. \n");
		}
	}
}
