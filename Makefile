all:
	mkdir -p RedundantLXC/usr/sbin/RedundantLXC_Tools
	mkdir -p RedundantLXC/usr/sbin/RedundantLXC
	cp -v src/main/*.py RedundantLXC/usr/sbin/RedundantLXC/
	cp -v src/main/*.json RedundantLXC/etc/
	cp -v src/tools/*.py RedundantLXC/usr/sbin/RedundantLXC_Tools/
	cp -v src/tools/launchers/* RedundantLXC/usr/sbin/
	chmod 0755 -Rv RedundantLXC/usr/
	chown root:root -Rv RedundantLXC/usr
	dpkg-deb --build RedundantLXC

clean:
	rm -v RedundantLXC/etc/*.json
	rm -v RedundantLXC/usr/sbin/RedundantLXC/*
	rm -v RedundantLXC/usr/sbin/RedundantLXC_Tools/*
	rm -v RedundantLXC/usr/sbin/LXC_*
	rm -v RedundantLXC.deb