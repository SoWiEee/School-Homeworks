public class Point {
	private double xCoor;
	private double yCoor;

	public Point() {
		this.xCoor = 0;
		this.yCoor = 0;
	}

	public Point(double xCoor, double yCoor) {
		this.xCoor = xCoor;
		this.yCoor = yCoor;
	}

	public void setXCoor(double xCoor) {
		this.xCoor = xCoor;
	}

	public double getXCoor() {
		return xCoor;
	}

	public void setYCoor(double yCoor) {
		this.yCoor = yCoor;
	}

	public double getYCoor() {
		return yCoor;
	}

	public String toString() {
		return String.format("(%.2f, %.2f)", xCoor, yCoor);
	}
}
