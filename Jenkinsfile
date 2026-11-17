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

        // --- Paths ---
        REPORT_DIR   = 'tests\\reports'
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
                // 2a. Verify Postgres (5432), backend (5000) and frontend (3000) are listening.
                //     Jenkins does not start them; you must start them locally first.
                powershell '''
                    $ports = @{ "PostgreSQL" = 5432; "Backend API" = 5000; "Frontend UI" = 3000 }
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
                    if not exist .venv ( python -m venv .venv || exit /b 1 )
                    if not exist %REPORT_DIR% mkdir %REPORT_DIR%

                    fc requirements.txt .venv\\requirements.installed >nul 2>&1
                    if errorlevel 1 (
                        echo requirements changed or first run - installing...
                        %PY% -m pip install -r requirements.txt || exit /b 1
                        %PY% -m playwright install chromium    || exit /b 1
                        copy /Y requirements.txt .venv\\requirements.installed >nul
                    ) else (
                        echo requirements unchanged - skipping install
                    )
                '''
            }
        }

        stage('3. Load Data') {
            steps {
                // Loads clean data so downstream tests start from a known state.
                // Replace with your real pipeline entry point.
                bat '%PY% pipeline\\run_pipeline.py --dataset good_data'
            }
        }

        stage('4. DQ Validation (UC1)') {
            steps {
                // No catchError here on purpose: if GX fails, the stage fails and
                // Jenkins skips every later stage. Bad data must not proceed.
                bat '%PY% tests\\dq\\run_gx.py'
            }
        }

        stage('5. API Tests (UC2)') {
            steps {
                // catchError marks the stage/build FAILED but lets the pipeline continue.
                catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
                    bat '%PY% -m pytest tests\\api --html=%REPORT_DIR%\\api_report.html --self-contained-html'
                }
            }
        }

        stage('6. UI Tests (UC3)') {
            steps {
                catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
                    bat '%PY% -m pytest tests\\ui --html=%REPORT_DIR%\\ui_report.html --self-contained-html'
                }
            }
        }

        stage('7. Pipeline Tests (UC4)') {
            steps {
                catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
                    bat '%PY% -m pytest tests\\pipeline --html=%REPORT_DIR%\\pipeline_report.html --self-contained-html'
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