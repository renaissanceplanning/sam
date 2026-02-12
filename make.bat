@ECHO OFF
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:: VARIABLES                                                                   ::
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
SETLOCAL EnableDelayedExpansion
SET "ENV_NAME=rp_base"
SET "ENV_FILE=build_environment.yml"

:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:: VALIDATION                                                                  ::
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:: Show help if no argument provided
IF "%~1"=="" (
    ECHO Usage: %~nx0 ^<command^>
    ECHO.
    ECHO Commands:
    ECHO   env            Build the conda environment from %ENV_FILE%
    ECHO   env_activate   Activate the %ENV_NAME% environment
    ECHO   env_remove     Remove the %ENV_NAME% environment
    EXIT /B 1
)

:: Validate the command is a known label
SET "VALID_CMD="
FOR %%C IN (env env_activate env_remove) DO (
    IF /I "%~1"=="%%C" SET "VALID_CMD=1"
)
IF NOT DEFINED VALID_CMD (
    ECHO ERROR: Unknown command "%~1"
    ECHO Run %~nx0 with no arguments to see available commands.
    EXIT /B 1
)

:: Verify conda is available
WHERE conda >NUL 2>&1
IF ERRORLEVEL 1 (
    ECHO ERROR: conda not found in PATH. Is Anaconda/Miniconda installed?
    EXIT /B 1
)

:: Jump to validated command
GOTO %~1

:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:: COMMANDS                                                                    ::
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

:: Build the local environment from the environment file
:env
    :: Check that required files exist
    IF NOT EXIST "%ENV_FILE%" (
        ECHO ERROR: Environment file "%ENV_FILE%" not found.
        EXIT /B 1
    )
    IF NOT EXIST "check_package_deps.py" (
        ECHO ERROR: check_package_deps.py not found.
        EXIT /B 1
    )

    :: Check if environment already exists
    CALL conda env list | FINDSTR /B /C:"%ENV_NAME% " >NUL 2>&1
    IF NOT ERRORLEVEL 1 (
        ECHO WARNING: Environment "%ENV_NAME%" already exists.
        SET /P "CONFIRM=Recreate it? [y/N]: "
        IF /I NOT "!CONFIRM!"=="y" (
            ECHO Aborted.
            EXIT /B 0
        )
        ECHO Removing existing environment...
        CALL conda env remove --name %ENV_NAME% -y || (
            ECHO ERROR: Failed to remove existing environment.
            EXIT /B 1
        )
    )

    ECHO Installing mamba solver...
    CALL conda install -c conda-forge mamba pyyaml -y || (
        ECHO ERROR: Failed to install mamba/pyyaml.
        EXIT /B 1
    )

    ECHO Updating package dependencies...
    CALL python check_package_deps.py --package || (
        ECHO ERROR: Package dependency check failed.
        EXIT /B 1
    )

    ECHO Creating environment from %ENV_FILE%...
    CALL mamba env create -f %ENV_FILE% || (
        ECHO ERROR: Environment creation failed.
        EXIT /B 1
    )

    ECHO.
    ECHO Environment "%ENV_NAME%" created successfully.
    ENDLOCAL & CALL conda activate %ENV_NAME%
    EXIT /B 0

:: Activate the environment
:env_activate
    :: Verify environment exists before activating
    CALL conda env list | FINDSTR /B /C:"%ENV_NAME% " >NUL 2>&1
    IF ERRORLEVEL 1 (
        ECHO ERROR: Environment "%ENV_NAME%" does not exist. Run "%~nx0 env" first.
        EXIT /B 1
    )
    ENDLOCAL & CALL conda activate %ENV_NAME%
    EXIT /B 0

:: Remove the environment
:env_remove
    :: Verify environment exists before removing
    CALL conda env list | FINDSTR /B /C:"%ENV_NAME% " >NUL 2>&1
    IF ERRORLEVEL 1 (
        ECHO Environment "%ENV_NAME%" does not exist. Nothing to remove.
        EXIT /B 0
    )

    SET /P "CONFIRM=Remove environment "%ENV_NAME%"? [y/N]: "
    IF /I NOT "!CONFIRM!"=="y" (
        ECHO Aborted.
        EXIT /B 0
    )

    ECHO Deactivating environment...
    ENDLOCAL
    CALL conda deactivate
    CALL conda activate base
    ECHO Removing environment...
    CALL conda env remove --name %ENV_NAME% -y || (
        ECHO ERROR: Failed to remove environment.
        EXIT /B 1
    )
    ECHO Environment removed successfully.
    EXIT /B 0