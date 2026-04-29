package ´Á¥½Q1;

public class RedDrug extends Drug{
	private int addLife;
	public RedDrug() {}
public RedDrug(String size) {
	super(size);
	switch(size) {
	case "large":
		addLife=120;
		break;
	case "medium":
		addLife=80;
		break;
	case "small":
		addLife=40;
		break;
		default:
	System.out.printf("No such size RedDrug->"+size);
		addLife=0;
	}
}
 public void setAddLife(int addLife) {
	 this.addLife=addLife;
 }
 public int getAddLife() {
	 return addLife;
 }
}
