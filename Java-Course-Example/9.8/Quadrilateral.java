public class Quadrilateral {
	private Point topRPoint;
	private Point topLPoint;
	private Point lowRPoint;
	private Point lowLPoint;

	public Quadrilateral() {
		this.topRPoint = new Point();
		this.topLPoint = new Point();
		this.lowRPoint = new Point();
		this.lowLPoint = new Point();
	}

	public Quadrilateral(Point topLPoint, Point topRPoint, Point lowRPoint, Point lowLPoint) {
		this.topRPoint = topRPoint;
		this.topLPoint = topLPoint;
		this.lowRPoint = lowRPoint;
		this.lowLPoint = lowLPoint;
	}

	public void setTopRPoint(Point topRPoint) {
		this.topRPoint = topRPoint;
	}

	public void setTopLPoint(Point topLPoint) {
		this.topLPoint = topLPoint;
	}

	public void setLowRPoint(Point lowRPoint) {
		this.lowRPoint = lowRPoint;
	}

	public void setLowLPoint(Point lowLPoint) {
		this.lowLPoint = lowLPoint;
	}

	public Point getTopRPoint() {
		return this.topRPoint;
	}

	public Point getTopLPoint() {
		return this.topLPoint;
	}

	public Point getLowRPoint() {
		return this.lowRPoint;
	}

	public Point getLowLPoint() {
		return this.lowLPoint;
	}

	public String toString() {
		return topRPoint.toString() + ", " + topLPoint.toString() + ", " + lowRPoint.toString() + ", " + lowRPoint.toString() + "\n";
	}
}
