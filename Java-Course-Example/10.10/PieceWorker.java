public class PieceWorker extends Employee {
	private double wage;
	private double pieces;

	public PieceWorker(String first, String last, String ssn, int month, int day, int year, double wage, double pieces) {
		super(first, last, ssn, month, day, year);
		setWage(wage);
		setPieces(pieces);
	}

	public void setWage(double wage) {
		this.wage = wage > 0.0 ? wage : 0.0;
	}

	public double getWage() {
		return wage;
	}

	public void setPieces(double pieces) {
		this.pieces = pieces > 0.0 ? pieces : 0.0;
	}

	public double getPieces() {
		return pieces;
	}

	@Override
	public double earnings() {
		return getWage() * getPieces();
	}

	public String toString() {
		return "\npiece work employee: " + super.toString();
	}
}
