package ´Á¥½Q1;

public class BlueDrug extends Drug{
	private int addMagic;
	public BlueDrug() {}
	public BlueDrug(String size) {
		super(size);
		switch(size) {
		case "large":
			addMagic = 100;
			break;
		case "medium":
			addMagic = 60;
			break;
		case "small":
			addMagic = 30;
			break;
			default:
				System.out.printf("No such size BlueDrug->"+size);
		}
	}
public void setAddMagic(int addMagic) {
	this.addMagic=addMagic;
}
public int getAddMagic() {
	return addMagic;
}
}
