# CalcUS - Computational Chemistry Web Platform
CalcUS is a computational chemistry plateform. It strives for simplicity, clarity and efficiency. It brings all the necessary tools to perform computational chemistry in a user-friendly web interface. 

This project is developed by the Legault group at the Université de Sherbrooke (Sherbrooke, Canada).

## Installation
Firstly, install and configure [Docker](https://www.docker.com/). On Linux, it is necessary to create a docker group and to add yourself to it:

`sudo groupadd docker
sudo usermod -aG docker $USER`

You will need to log out and log back in for the changes to be effective.

Then, clone the repository. In that repository, a file named `.env` will be needed to set the necessary environment variables. The script `generate_env.py` can be used to interactively create that file. Simply run it with the command `python3 generate_env.py` and answer the questions. When you will run CalcUS, a superuser account will be created with the username specified in the `.env` file. You can use this account as main account, but make sure to change the password if the server is accessible to others.

Also note that the `.env` *contains sensitive information* and should only be accessible by the server administrator.
	
## Running CalcUS
Once the setup is complete, build the docker image using `docker-compose build`, and launch it using `docker-compose up`. CalcUS is now available in your web browser at the address `0.0.0.0:8080`. You might need to manually start the docker service if you've just installed it. It will start automatically at boot in the future.

Further documentation is available in CalcUS itself.

## Contributors
**Project lead and main contributor**: Raphaël Robidas

**Contributor to the conception and beta-testing*: Prof. Claude Y. Legault

**Beta-testers**:

+ Léo Hall
+ Joanick Bourret
+ David Lemire
+ Tommy Lussier
+ Louis Schutz

## Dependencies
CalcUS makes use of several third-party softwares. For convenience, all the non-Python packages are redistributed in this repository, along with their license and/or links to their homepage. These packages are however not part of CalcUS itself.

## License
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see https://www.gnu.org/licenses/.

CalcUS - Computational Chemistry Web Platform

Copyright (C) 2021 Raphaël Robidas
