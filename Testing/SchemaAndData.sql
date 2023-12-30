CREATE DATABASE  IF NOT EXISTS `RedundantLXC` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci */;
USE `RedundantLXC`;
-- MariaDB dump 10.19  Distrib 10.6.12-MariaDB, for debian-linux-gnu (x86_64)
--
-- Host: 127.0.0.1    Database: RedundantLXC
-- ------------------------------------------------------
-- Server version	10.6.12-MariaDB-0ubuntu0.22.04.1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `ContainerStatus`
--

DROP TABLE IF EXISTS `ContainerStatus`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ContainerStatus` (
  `NID` int(11) NOT NULL,
  `CID` int(11) NOT NULL,
  PRIMARY KEY (`CID`),
  KEY `NID` (`NID`),
  CONSTRAINT `ContainerStatus_ibfk_1` FOREIGN KEY (`NID`) REFERENCES `Nodes` (`NID`),
  CONSTRAINT `ContainerStatus_ibfk_2` FOREIGN KEY (`CID`) REFERENCES `Containers` (`CID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ContainerStatus`
--

LOCK TABLES `ContainerStatus` WRITE;
/*!40000 ALTER TABLE `ContainerStatus` DISABLE KEYS */;
INSERT INTO `ContainerStatus` VALUES (1,3),(2,2),(4,1);
/*!40000 ALTER TABLE `ContainerStatus` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Containers`
--

DROP TABLE IF EXISTS `Containers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Containers` (
  `CID` int(11) NOT NULL,
  `Name` varchar(64) NOT NULL,
  `Priority` int(11) NOT NULL,
  `Cost` int(11) NOT NULL,
  `Zone` int(11) NOT NULL,
  `Arch` varchar(16) DEFAULT NULL,
  PRIMARY KEY (`CID`),
  KEY `Zone` (`Zone`),
  CONSTRAINT `Containers_ibfk_1` FOREIGN KEY (`Zone`) REFERENCES `Zones` (`ZID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Containers`
--

LOCK TABLES `Containers` WRITE;
/*!40000 ALTER TABLE `Containers` DISABLE KEYS */;
INSERT INTO `Containers` VALUES (1,'Test',100,250,1,'x64'),(2,'Test2',100,250,1,'x64'),(3,'Test3',100,500,1,'x64');
/*!40000 ALTER TABLE `Containers` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `FlaggedContainers`
--

DROP TABLE IF EXISTS `FlaggedContainers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `FlaggedContainers` (
  `CID` int(11) NOT NULL,
  `NID` int(11) DEFAULT NULL,
  `Time` bigint(255) NOT NULL,
  PRIMARY KEY (`CID`),
  CONSTRAINT `FlaggedContainers_ibfk_1` FOREIGN KEY (`CID`) REFERENCES `Containers` (`CID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `FlaggedContainers`
--

LOCK TABLES `FlaggedContainers` WRITE;
/*!40000 ALTER TABLE `FlaggedContainers` DISABLE KEYS */;
/*!40000 ALTER TABLE `FlaggedContainers` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `NodeStatus`
--

DROP TABLE IF EXISTS `NodeStatus`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `NodeStatus` (
  `NID` int(11) NOT NULL,
  `LastSeen` bigint(255) NOT NULL,
  PRIMARY KEY (`NID`),
  CONSTRAINT `NodeStatus_ibfk_1` FOREIGN KEY (`NID`) REFERENCES `Nodes` (`NID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `NodeStatus`
--

LOCK TABLES `NodeStatus` WRITE;
/*!40000 ALTER TABLE `NodeStatus` DISABLE KEYS */;
INSERT INTO `NodeStatus` VALUES (1,1703909355),(2,1703909352),(3,1703909352),(4,1703909353);
/*!40000 ALTER TABLE `NodeStatus` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Nodes`
--

DROP TABLE IF EXISTS `Nodes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Nodes` (
  `NID` int(11) NOT NULL,
  `Name` varchar(64) NOT NULL,
  `Budget` int(11) NOT NULL,
  `Arch` varchar(16) DEFAULT NULL,
  PRIMARY KEY (`NID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Nodes`
--

LOCK TABLES `Nodes` WRITE;
/*!40000 ALTER TABLE `Nodes` DISABLE KEYS */;
INSERT INTO `Nodes` VALUES (1,'LXD1',1000,'x64'),(2,'LXD2',2000,'x64'),(3,'LXD3',1000,'x64'),(4,'LXD4',1000,'x64');
/*!40000 ALTER TABLE `Nodes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ZoneMembership`
--

DROP TABLE IF EXISTS `ZoneMembership`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZoneMembership` (
  `ZID` int(11) NOT NULL,
  `NID` int(11) NOT NULL,
  PRIMARY KEY (`ZID`,`NID`),
  KEY `NID` (`NID`),
  CONSTRAINT `ZoneMembership_ibfk_1` FOREIGN KEY (`ZID`) REFERENCES `Zones` (`ZID`),
  CONSTRAINT `ZoneMembership_ibfk_2` FOREIGN KEY (`NID`) REFERENCES `Nodes` (`NID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ZoneMembership`
--

LOCK TABLES `ZoneMembership` WRITE;
/*!40000 ALTER TABLE `ZoneMembership` DISABLE KEYS */;
INSERT INTO `ZoneMembership` VALUES (1,1),(1,2),(1,3),(1,4);
/*!40000 ALTER TABLE `ZoneMembership` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Zones`
--

DROP TABLE IF EXISTS `Zones`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Zones` (
  `ZID` int(11) NOT NULL,
  `Name` varchar(64) NOT NULL,
  PRIMARY KEY (`ZID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Zones`
--

LOCK TABLES `Zones` WRITE;
/*!40000 ALTER TABLE `Zones` DISABLE KEYS */;
INSERT INTO `Zones` VALUES (1,'MainZone');
/*!40000 ALTER TABLE `Zones` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2023-12-30 15:09:15
