create database if not exists RedundantLXC ;
use RedundantLXC;

create table if not exists Nodes(
	`NID` INT NOT NULL,
    `Name` VARCHAR(64) NOT NULL,
    `Budget` INT NOT NULL,
    `Arch` VARCHAR(16),
    PRIMARY KEY(`NID`)
);
create table if not exists Zones(
	`ZID` INT NOT NULL,
    `Name` VARCHAR(64) NOT NULL,
    PRIMARY KEY(`ZID`)
);
create table if not exists Containers(
	`CID` INT NOT NULL,
    `Name` VARCHAR(64) NOT NULL,
    `Priority` INT NOT NULL,
    `Cost` INT NOT NULL,
    `Zone` INT NOT NULL,
    `Arch` VARCHAR(16),
    PRIMARY KEY(`CID`),
    FOREIGN KEY(`Zone`) REFERENCES Zones(`ZID`)
);
create table if not exists ZoneMembership(
	`ZID` INT NOT NULL,
    `NID` INT NOT NULL,
    PRIMARY KEY(`ZID`,`NID`),
    FOREIGN KEY(`ZID`) REFERENCES Zones(`ZID`),
    FOREIGN KEY(`NID`) REFERENCES Nodes(`NID`)
);
create table if not exists ContainerStatus(
	`NID` INT NOT NULL,
    `CID` INT NOT NULL,
    PRIMARY KEY(`CID`),
    FOREIGN KEY(`NID`) REFERENCES Nodes(`NID`),
    FOREIGN KEY(`CID`) REFERENCES Containers(`CID`)
);

create table if not exists FlaggedContainers(
	`CID` INT NOT NULL,
    `NID` INT,
    `Time` BIGINT(255) NOT NULL,
    PRIMARY KEY(`CID`),
    FOREIGN KEY(`CID`) REFERENCES Containers(`CID`)
);

create table if not exists NodeStatus(
	`NID` INT NOT NULL,
    `LastSeen` BIGINT(255) NOT NULL,
    PRIMARY KEY(`NID`),
    FOREIGN KEY(`NID`) REFERENCES Nodes(`NID`)
);