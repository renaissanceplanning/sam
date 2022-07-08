:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:: LICENSING                                                                    :
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
::
:: Copyright 2020 Esri
::
:: Licensed under the Apache License, Version 2.0 (the "License"); You
:: may not use this file except in compliance with the License. You may
:: obtain a copy of the License at
::
:: http://www.apache.org/licenses/LICENSE-2.0
::
:: Unless required by applicable law or agreed to in writing, software
:: distributed under the License is distributed on an "AS IS" BASIS,
:: WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
:: implied. See the License for the specific language governing
:: permissions and limitations under the License.
::
:: A copy of the license is available in the repository's
:: LICENSE file.

:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:: VARIABLES                                                                    :
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

SETLOCAL
SET PROJECT_DIR=%cd%
SET PROJECT_NAME=sam
SET SUPPORT_LIBRARY=sam
SET ENV_NAME=sam

:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:: COMMANDS                                                                     :
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

:: Jump to command
GOTO %1

:: Make documentation using Sphinx!
:docs
    ENDLOCAL & (
        CALL docsrc/make.bat github
    )
	EXIT /B

:: Build the local environment from the environment file
:env
    ENDLOCAL & (
        :: Ensure mamba installed in root env
        ECHO Installing mamba...
        CALL conda install mamba pyyaml -c conda-forge -y
        :: Run the update tool for the build conda environment
        ECHO Updating build environment...
        CALL python check_package_deps.py
        :: Create new environment from environment file
        ECHO Creating new environment...
        CALL mamba env create -f build_environment.yml
        :: Activate the environment so you can get to work
        ECHO Activating new environment...
        CALL activate "%ENV_NAME%"
        :: Install the local package in development (experimental) mode
        ECHO Installing local package in development mode..."%ENV_NAME%"
        CALL python -m pip install -e .
    )
    EXIT /B

:: Activate the environment
:env_activate
    ENDLOCAL & CALL activate "%ENV_NAME%"
    EXIT /B

:: Remove the environment
:env_remove
	ENDLOCAL & (
		CALL conda deactivate
		CALL conda env remove --name "%ENV_NAME%" -y
	)
	EXIT /B

:: Build the local environment from the environment file
:add_spyder
    ENDLOCAL & (
        :: activate environment
        CALL activate "%ENV_NAME%"
        :: Ensure mamba installed in root env
        CALL conda install -c anaconda spyder
        :: deactivate environment
        CALL deactivate "%ENV_NAME%"
    )
    EXIT /B

EXIT /B
