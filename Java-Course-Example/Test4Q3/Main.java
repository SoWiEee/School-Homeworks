import javax.swing.*;
import java.awt.*;

public class Main {
    // create a frame (window)
    static JFrame frm = new JFrame("DSG Calculator");

    static JPanel num = new JPanel(new GridLayout(3,3));
    static JPanel oper = new JPanel(new GridLayout(4,1));
    static JPanel side = new JPanel(new GridLayout(2,1));
    static JLabel monitor = new JLabel("0 ", JLabel.RIGHT);
    static JLabel title = new JLabel("DSG Calculator", JLabel.LEFT);

    static JButton btn_eq = new JButton("=");
    static JButton btn_clr = new JButton("Clear");
    static JButton btn_zero = new JButton("0");
    static JButton btn_dot = new JButton(".");

    // font
    static Font fnt_monitor = new Font("Serif", Font.BOLD, 24);
    static Font fnt_title = new Font("SansSerif", Font.BOLD + Font.ITALIC, 12);
    static Font fnt_num = new Font("Serif", Font.BOLD, 16);
    static Font fnt_oper = new Font("SansSerif", Font.BOLD, 20);
    static Font fnt_eq = new Font("SansSerif", Font.BOLD, 24);
    static Font fnt_clr = new Font("SansSerif", Font.BOLD, 16);

    public static void main(String[] args) {
        // windows
        frm.setLayout(null);
        frm.setSize(370, 243);
        frm.setResizable(false);    // fix window size

        // monitor
        monitor.setBounds(26, 10, 210, 40);
        monitor.setOpaque(true);
        monitor.setBackground(Color.pink);
        monitor.setFont(fnt_monitor);

        // num
        num.setBounds(26, 59, 150, 100);

        // title
        title.setBounds(251, 11, 95, 40);
        title.setFont(fnt_title);

        // oper
        oper.setBounds(186, 59, 50, 133);

        // side
        btn_eq.setBounds(251, 59,72, 62);
        btn_clr.setBounds(251, 128, 72, 62);
        btn_zero.setBounds(26, 157, 100, 33);
        btn_dot.setBounds(126, 157, 50, 33);

        // add number buttons
        for(int i = 1; i <= 9; i++) {
            JButton btn = new JButton(Integer.toString(i));
            btn.setFont(fnt_num);
            num.add(btn);
        }

        // add operator buttons

        String[] opArr = { "+", "-", "x", "/" };
        for(String op : opArr){
            JButton btn = new JButton(op);
            btn.setFont(fnt_oper);
            oper.add(btn);
        }

        // add side buttons
        btn_eq.setFont(fnt_eq);
        btn_clr.setFont(fnt_clr);
        btn_zero.setFont(fnt_num);
        btn_dot.setFont(fnt_num);

        // embeding
        frm.add(monitor);
        frm.add(num);
        frm.add(oper);
        frm.add(btn_eq);
        frm.add(btn_clr);
        frm.add(btn_zero);
        frm.add(btn_dot);
        frm.add(title);

        frm.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        frm.setVisible(true);
    }
}