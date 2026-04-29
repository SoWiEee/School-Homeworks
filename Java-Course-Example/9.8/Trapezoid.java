public class Trapezoid extends Quadrilateral {
	public Trapezoid(Point p1, Point p2, Point p3, Point p4) {
		super(p1, p2, p3, p4);
	}

	public double getHeight() {
		return Math.abs(getTopLPoint().getYCoor() - getLowLPoint().getYCoor());
	}

	public double getSumOfTwoSide() {
		return Math.abs(getTopLPoint().getXCoor() - getTopRPoint().getXCoor()) + Math.abs(getLowLPoint().getXCoor() - getLowRPoint().getXCoor());
	}

	public double getArea() {
		return getHeight() * getSumOfTwoSide() / 2.0;
	}

	public String toString() {
		return String.format("Trapezoid Area: %.2f\n", getArea());
	}
}
