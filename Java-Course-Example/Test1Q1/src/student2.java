
public class student2 {
	
	private int test[] = new int [3];
	
	public student2() {
		test[0]=(int)(Math.random()*100)+1;
		test[1]=(int)(Math.random()*100)+1;
		test[2]=(int)(Math.random()*100)+1;
	}
	
	public int get_test(int i){
		return test[i];
	}
	public double get_aver() {
		return (test[0]+test[1]+test[2]/3.0);
	}

}
