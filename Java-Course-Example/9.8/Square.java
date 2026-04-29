public class Square extends Rectangle {
	public Square(Point p1, Point p2, Point p3, Point p4) {
		super(p1, p2, p3, p4);
	}

	public String toString() {
		return String.format("Square Area: %.2f\n", getArea());
	}
}
