public class Parallelogram extends Trapezoid {
	public Parallelogram(Point p1, Point p2, Point p3, Point p4) {
		super(p1, p2, p3, p4);
	}

	public double getWidth() {
		return Math.abs(getTopLPoint().getXCoor() - getTopRPoint().getXCoor());
	}

	public String toString() {
		return String.format("Parallelogram Area: %.2f\n", getArea());
	}
}
