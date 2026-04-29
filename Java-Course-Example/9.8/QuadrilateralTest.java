public class QuadrilateralTest {
	public static void main(String[] args) {
		Quadrilateral quadrilateral = new Quadrilateral(new Point(0, 10), new Point(5.5, 10), new Point(19.2, 0), new Point(0, 0));
		Trapezoid trapezoid = new Trapezoid(new Point(0, 10), new Point(5.5, 10), new Point(19.2, 0), new Point(0, 0));
		Parallelogram parallelogram = new Parallelogram(new Point(0, 10), new Point(12.35, 10), new Point(5.5, 0), new Point(17.85, 0));
		Rectangle rectangle = new Rectangle(new Point(0, 10), new Point(5.5, 10), new Point(5.5, 0), new Point(0, 0));
		Square square = new Square(new Point(0, 55), new Point(55, 55), new Point(55, 0), new Point(0, 0));

		System.out.println("quadrilateral coordinates is " + quadrilateral.toString());
		System.out.println("trapezoid area is " + trapezoid.toString());
		System.out.println("parallelogram area is " + parallelogram.toString());
		System.out.println("rectangle area is " + rectangle.toString());
		System.out.println("square area is " + square.toString());
	}
}
