#Create some Nodes
insert into Nodes(`NID`,`Name`,`Budget`,`Arch`,`LastSeen`) values (1,"One",1000,"arm",20);
insert into Nodes(`NID`,`Name`,`Budget`,`Arch`,`LastSeen`) values (2,"Two",4000,"arm",20);
insert into Nodes(`NID`,`Name`,`Budget`,`Arch`,`LastSeen`) values (3,"Three",8000,"arm",20);

#Create the Zones
insert into Zones(`ZID`,`Name`) values (1,"Default");
insert into Zones(`ZID`,`Name`) values (2,"Performance");

#Add Nodes to the Zones
insert into ZoneMembership(`ZID`,`NID`) values (1,1);
insert into ZoneMembership(`ZID`,`NID`) values (1,2);
insert into ZoneMembership(`ZID`,`NID`) values (1,3);

insert into ZoneMembership(`ZID`,`NID`) values (2,2);
insert into ZoneMembership(`ZID`,`NID`) values (2,3);

#Add the Containers
insert into Containers(`CID`,`Name`,`Priority`,`Cost`,`Zone`,`Arch`) values (1,"First",100,100,1,"arm");
insert into Containers(`CID`,`Name`,`Priority`,`Cost`,`Zone`,`Arch`) values (2,"Second",50,200,1,"arm");
insert into Containers(`CID`,`Name`,`Priority`,`Cost`,`Zone`,`Arch`) values (3,"Third",400,400,2,"arm");
insert into Containers(`CID`,`Name`,`Priority`,`Cost`,`Zone`,`Arch`) values (4,"Fourth",400,400,1,"arm");

#Update the Status
insert into ContainerStatus(`NID`,`CID`) values (1,1);
insert into ContainerStatus(`NID`,`CID`) values (3,2);
insert into ContainerStatus(`NID`,`CID`) values (3,3);
insert into ContainerStatus(`NID`,`CID`) values (2,4);