pipeline {
    agent any

    options {
        timestamps()                       // prefix console lines with time
        timeout(time: 30, unit: 'MINUTES') // kill hung builds
    }

    environment {
        // --- Connection details used by the tests ---
        DB_HOST      = 'localhost'
        DB_PORT      = '5432'
        DB_NAME      = 'fincore'
        DB_CREDS     = credentials('fincore-db-creds') // gives DB_CREDS_USR / DB_CREDS_PSW
        API_BASE_URL = 'http://localhost:4000/api/v1'
        UI_BASE_URL  = 'http://localhost:3000'
        VITE_API_URL = '/api/v1'
        PYTHON_EXE = 'C:\\Users\\Ranjith_Akula\\AppData\\Local\\Programs\\Python\\Python311\\python.exe'
        // JAVA_HOME = "C:\\Program Files\\Common Files\\Oracle\\Java\\javapath\\java.exe"
        JAVA_HOME = 'C:\\java\\jdk'
        // PATH      = "${WORKSPACE}\\.venv\\Scripts;${JAVA_HOME}\\bin;${env.PATH}"
        // PATH      = "${WORKSPACE}\\.venv\\Scripts;${JAVA_HOME}\\bin;${env.PATH}"
        // PySpark's launcher looks for "python3" by default; Windows only has python.exe.
        PYSPARK_PYTHON        = "${WORKSPACE}\\.venv\\Scripts\\python.exe"
        PYSPARK_DRIVER_PYTHON = "${WORKSPACE}\\.venv\\Scripts\\python.exe"
        // SPARK_HOME            = "${WORKSPACE}\\.venv\\Lib\\site-packages\\pyspark"
        HADOOP_HOME = 'C:\\hadoop'
        PATH = "${WORKSPACE}\\.venv\\Scripts;${JAVA_HOME}\\bin;${HADOOP_HOME}\\bin;${env.PATH}"

        // --- Paths ---
        REPORT_DIR   = 'tests\\reports'
        LOCAL_REPORT_DIR = 'C:\\Users\\Ranjith_Akula\\Documents\\GitHub\\Test_Automation_Fincore_Backup\\tests\\reports'
        PY           = '.venv\\Scripts\\python'   // always use the venv's python
        NOTIFY_EMAIL = 'ranjithguptha111@gmail.com'
    }

    stages {

        stage('1. Checkout') {
            steps {
                // Pulls latest code from the repo configured in the job.
                // Failure aborts the pipeline: no code, no tests.
                checkout scm
            }
        }

        stage('2. Environment Check') {
            steps {
                // 2a. Verify Postgres (5432), backend (4000) and frontend (3000) are listening.
                //     Jenkins does not start them; you must start them locally first.
                powershell '''
                    $ports = @{ "PostgreSQL" = 5432; "Backend API" = 4000; "Frontend UI" = 3000 }
                    $failed = $false
                    foreach ($name in $ports.Keys) {
                        $ok = (Test-NetConnection -ComputerName localhost -Port $ports[$name] -WarningAction SilentlyContinue).TcpTestSucceeded
                        if ($ok) { Write-Host "OK   : $name on port $($ports[$name])" }
                        else     { Write-Host "DOWN : $name on port $($ports[$name])"; $failed = $true }
                    }
                    if ($failed) { exit 1 }   # abort: environment not ready
                '''

                // 2b. Create the venv only if it doesn't exist yet.
                // 2c. Reinstall only when requirements.txt differs from the copy saved
                //     after the last successful install (fc returns non-zero if they differ).
                bat '''
					if not exist .venv ( "%PYTHON_EXE%" -m venv .venv || exit /b 1 )
					if not exist %REPORT_DIR% mkdir %REPORT_DIR%
				
					rem Merge every requirements file into one (edit this list to match your repo)
					(for %%f in (data\\requirements.txt pipeline\\requirements.txt) do @(type %%f & echo.)) > .venv\\requirements.combined
				
					rem Reinstall only if the merged list changed since the last successful install
					fc .venv\\requirements.combined .venv\\requirements.installed >nul 2>&1
					if errorlevel 1 (
						echo requirements changed or first run - installing...
						%PY% -m pip install -r .venv\\requirements.combined || exit /b 1
						%PY% -m playwright install chromium                 || exit /b 1
						copy /Y .venv\\requirements.combined .venv\\requirements.installed >nul
					) else (
						echo requirements unchanged - skipping install
					)
				'''	
            }
        }


        stage('3. Load Data') {
			steps {
				// 3a. Generate test data. The script's own hint says to run it from inside data\,
				//     so run it there to make sure its output lands in data\good_data.
				// dir('data') {
				// 	powershell '''
				// 		& ..\\.venv\\Scripts\\python generate_data.py
				// 		if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
				// 	'''
				// }
                // temp step to check path issue
                powershell '''
                    Write-Host "JAVA_HOME      = $env:JAVA_HOME"
                    Write-Host "SPARK_HOME     = $env:SPARK_HOME"
                    Write-Host "PYSPARK_PYTHON = $env:PYSPARK_PYTHON"
                    Test-Path "$env:JAVA_HOME\\bin\\java.exe"
                    Test-Path "$env:SPARK_HOME\\bin\\spark-submit.cmd"
                    Test-Path "$env:PYSPARK_PYTHON"
                    Get-ChildItem -Directory pipeline | Select-Object Name   # is there a venv folder here?
                '''
		
				// 3b. Load good_data into PostgreSQL. run_pipeline.ps1 resolves ..\\data\\good_data
				//     relative to its own folder, so run it from inside pipeline\\.
				dir('pipeline') {
					powershell '''
						& .\\run_pipeline.ps1 -DataFolder good_data
						if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
					'''
				}
			}
		}

        stage('4. DQ Validation (UC1)') {
            steps {
                powershell '''
                    $gxRoot = Join-Path $env:WORKSPACE 'tests\\dq\\great_expectations\\gx'
                    $configDirectory = Join-Path $gxRoot 'uncommitted'
                    $configPath = Join-Path $configDirectory 'config_variables.yml'
                    $dbUser = [uri]::EscapeDataString($env:DB_CREDS_USR)
                    $dbPassword = [uri]::EscapeDataString($env:DB_CREDS_PSW)
                    $connectionString = "postgresql+psycopg2://${dbUser}:${dbPassword}@$($env:DB_HOST):$($env:DB_PORT)/$($env:DB_NAME)"
                    $configContent = "fincore_pg_conn: '$connectionString'"

                    New-Item -ItemType Directory -Force -Path $configDirectory | Out-Null
                    Set-Content -Path $configPath -Value $configContent -Encoding ascii

                    try {
                        & .venv\\Scripts\\python tests\\dq\\run_gx.py
                        $pythonExitCode = $LASTEXITCODE
                    } finally {
                        Remove-Item -LiteralPath $configPath -Force -ErrorAction SilentlyContinue
                    }

                    if ($pythonExitCode -ne 0) { exit $pythonExitCode }
                '''
            }
        }

        stage('5. API Tests (UC2)') {
            steps {
                // catchError marks the stage/build FAILED but lets the pipeline continue.
                catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
                    withCredentials([usernamePassword(
                        credentialsId: 'fincore-api-test-user',
                        usernameVariable: 'TEST_USER_USERNAME',
                        passwordVariable: 'TEST_USER_PASSWORD'
                    )]) {
                        powershell '''
                            $dbUser = [uri]::EscapeDataString($env:DB_CREDS_USR)
                            $dbPassword = [uri]::EscapeDataString($env:DB_CREDS_PSW)
                            $env:DATABASE_URL = "postgresql://${dbUser}:${dbPassword}@$($env:DB_HOST):$($env:DB_PORT)/$($env:DB_NAME)"

                            & .venv\\Scripts\\python -m pytest tests\\api "--html=$($env:REPORT_DIR)\\api_report.html" --self-contained-html
                            if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
                        '''
                    }
                }
            }
        }

        stage('6. UI Tests (UC3)') {
            steps {
                catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
                    withCredentials([usernamePassword(
                        credentialsId: 'fincore-api-test-user',
                        usernameVariable: 'TEST_USER_USERNAME',
                        passwordVariable: 'TEST_USER_PASSWORD'
                    )]) {
                        powershell '''
                            $dbUser = [uri]::EscapeDataString($env:DB_CREDS_USR)
                            $dbPassword = [uri]::EscapeDataString($env:DB_CREDS_PSW)
                            $env:DATABASE_URL = "postgresql://${dbUser}:${dbPassword}@$($env:DB_HOST):$($env:DB_PORT)/$($env:DB_NAME)"
                            $env:FINCORE_BASE_URL = $env:UI_BASE_URL

                            & .venv\\Scripts\\python -m pytest tests\\ui "--html=$($env:REPORT_DIR)\\ui_report.html" --self-contained-html
                            if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
                        '''
                    }
                }
            }
        }

        stage('7. Pipeline Tests (UC4)') {
            steps {
                catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
                    withCredentials([usernamePassword(
                        credentialsId: 'fincore-api-test-user',
                        usernameVariable: 'TEST_USER_USERNAME',
                        passwordVariable: 'TEST_USER_PASSWORD'
                    )]) {
                        powershell '''
                            $dbUser = [uri]::EscapeDataString($env:DB_CREDS_USR)
                            $dbPassword = [uri]::EscapeDataString($env:DB_CREDS_PSW)
                            $env:DATABASE_URL = "postgresql://${dbUser}:${dbPassword}@$($env:DB_HOST):$($env:DB_PORT)/$($env:DB_NAME)"
                            $env:DB_USER = $env:DB_CREDS_USR
                            $env:DB_PASSWORD = $env:DB_CREDS_PSW
                            $env:FINCORE_BASE_URL = $env:UI_BASE_URL

                            $gxRoot = Join-Path $env:WORKSPACE 'tests\\dq\\great_expectations\\gx'
                            $configDirectory = Join-Path $gxRoot 'uncommitted'
                            $configPath = Join-Path $configDirectory 'config_variables.yml'
                            $gxConfigContent = "fincore_pg_conn: '$($env:DATABASE_URL -replace '^postgresql://', 'postgresql+psycopg2://')'"

                            New-Item -ItemType Directory -Force -Path $configDirectory | Out-Null
                            Set-Content -Path $configPath -Value $gxConfigContent -Encoding ascii

                            try {
                                & .venv\\Scripts\\python -m pytest tests\\pipeline\\test_transformations.py "--html=$($env:REPORT_DIR)\\pipeline_report.html" --self-contained-html
                                $pythonExitCode = $LASTEXITCODE
                            } finally {
                                Remove-Item -LiteralPath $configPath -Force -ErrorAction SilentlyContinue
                            }

                            if ($pythonExitCode -ne 0) { exit $pythonExitCode }
                        '''
                    }
                }
            }
        }

        stage('8. Archive Reports') {
            steps {
                // Warning only: if archiving fails, mark the stage UNSTABLE, not the build FAILED.
                catchError(buildResult: 'SUCCESS', stageResult: 'UNSTABLE') {
                    archiveArtifacts artifacts: 'tests/reports/**/*.html, gx/uncommitted/data_docs/**/*',
                                     allowEmptyArchive: false
                }
            }
        }

        stage('9. Notify') {
            steps {
                echo "Build #${env.BUILD_NUMBER} status: ${currentBuild.currentResult}"
            }
        }
    }

    // Post block runs after all stages, even when the pipeline aborted early.
    post {
        always {
            // Safety net: if stage 4 aborted, stages 8-9 were skipped,
            // so archive whatever reports exist and print the final status here too.
            archiveArtifacts artifacts: 'tests/reports/**/*.html, gx/uncommitted/data_docs/**/*',
                             allowEmptyArchive: true
            echo "Final status: ${currentBuild.currentResult}"
            powershell '''
                $source = Join-Path $env:WORKSPACE 'tests\\reports'
                $destination = $env:LOCAL_REPORT_DIR

                if (-not (Test-Path -LiteralPath $source -PathType Container)) {
                    throw "Report source directory does not exist: $source"
                }

                New-Item -ItemType Directory -Force -Path $destination | Out-Null
                Copy-Item -Path (Join-Path $source '*') -Destination $destination -Recurse -Force
                Write-Host "Reports copied to $destination"
            '''
        }
        success {
            echo 'All stages passed.'
        }
        failure {
            // Needs SMTP configured under Manage Jenkins > System
            mail to: "${env.NOTIFY_EMAIL}",
                 subject: "FAILED: ${env.JOB_NAME} #${env.BUILD_NUMBER}",
                 body: "Build failed. Details: ${env.BUILD_URL}"
        }
    }
}