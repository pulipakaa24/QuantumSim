OPENQASM 2.0;

    include "qelib1.inc";

    qreg q[3];
    creg c[3];
if (c == 0) ch q[0], q[1];
cy q[0], q[2];
measure q[0] -> c[0];
measure q[1] -> c[1];
    measure q[2] -> c[2];
rx(pi/2) q[0];
rz(pi/2) q[0];
u(pi/2, pi/2, pi/2) q[1];
rz(pi/2) q[0];
