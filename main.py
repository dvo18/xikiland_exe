import sys
import json
import shutil
import subprocess
import win32com.client

from pathlib import Path
from tkinter import Tk, messagebox
from datetime import datetime, timezone
from git import Repo, GitCommandError,InvalidGitRepositoryError

#prueba


instance_name = 'client_XIKILAND2'

git_repo = "https://github.com/dvo18/XIKILAND.git"

CF_install_path = Path.home() / 'curseforge' / 'minecraft' / 'Install'
CF_instnace_path = Path.home() / 'curseforge' / 'minecraft' / 'Instances' / instance_name


command_list = [f'{CF_install_path}/minecraft.exe', '--workDir', CF_install_path]

git_dirs = [ '.git', '.gitignore', '.gitattributes', 'README.md', 
            'mods', 'resourcepacks', 'shaderpacks', 
            'config/fancymenu', 'config/missions', 
            'config/.gitignore', 
            '_XIKILAND-data' ]


def show_end_alert(message, error=True):
    root = Tk()
    root.withdraw()
    
    if error:
        messagebox.showerror("Error", message)
    else:
        messagebox.showinfo("Información", message)
    
    root.destroy()
    sys.exit(1)


def create_shortcut(executable_path):
    shortcut_path = Path.home() / 'Desktop' / 'XIKILAND.lnk'

    if shortcut_path.exists():
        print(f"El acceso directo ya existe en: {shortcut_path}")
        return

    try:
        shell = win32com.client.Dispatch("WScript.Shell")

        shortcut = shell.CreateShortCut(str(shortcut_path))

        shortcut.Targetpath = str(executable_path)
        shortcut.WorkingDirectory = str(executable_path.parent)

        shortcut.save()

        print(f"Acceso directo creado en: {shortcut_path}")
        
    except Exception as e:
        show_end_alert(f"No se pudo crear el acceso directo: {e}")


def initializate():
    launcher_path = Path.home() / 'AppData' / 'Roaming' / '.xikiLauncher'
 
    try:
        if not launcher_path.exists():
            print(f"Creando el directorio {launcher_path}")
            launcher_path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        show_end_alert(f"No se pudo crear el directorio {launcher_path}: {e}")
    
    current_executable = Path(sys.argv[0]).resolve()
    target_executable = launcher_path / current_executable.name
    
    if current_executable != target_executable:
        try:
            print(f"Moviendo el ejecutable desde {current_executable} a {target_executable}")
            shutil.move(str(current_executable), str(target_executable))

            create_shortcut(target_executable)

            print(f"Reiniciando el programa desde {target_executable}")
            try:
                print(f"Reiniciando el programa desde {target_executable}")
                # subprocess.run([str(target_executable)] + sys.argv[1:], check=True)

            except subprocess.CalledProcessError as e:
                show_end_alert(f"Error al reiniciar el programa: {e}")
            except Exception as e:
                show_end_alert(f"Error inesperado al reiniciar el programa: {e}")
            
            sys.exit(0)
            
        except Exception as e:
            show_end_alert(f"Error moviendo el ejecutable: {e}")


def profiles_management():
    profiles_path = Path(CF_install_path) / 'launcher_profiles.json'
    old_profiles_path = Path(CF_install_path) / 'launcher_profiles_old.json'

    if not profiles_path.exists():
        show_end_alert("No se ha encontrado el archivo de perfiles de CurseForge\n"
                       "Se necesita iniciar el perfil a mano en CurseForge al menos una vez")

    try:
        with open(profiles_path, 'r') as f:
            profiles = json.load(f)
        
        if 'profiles' not in profiles:
            show_end_alert("No se encontró la sección 'profiles' en el archivo.")

        if instance_name in profiles['profiles']:
            shutil.copy2(profiles_path, old_profiles_path)
        else:
            if old_profiles_path.exists():
                shutil.copy2(old_profiles_path, profiles_path)
            else:
                current_time = datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')

                target_profile = None
                for profile in profiles['profiles'].values():
                    if 'javaArgs' in profile and 'resolution' in profile:
                        target_profile = profile
                        break

                if not target_profile:
                    show_end_alert("No se encontraron valores por defecto para iniciar el perfil\n"
                                   "Se necesita iniciar el perfil a mano en CurseForge al menos una vez")

                java_args = target_profile['javaArgs'].split()
                xmx_arg = next((arg for arg in java_args if arg.startswith('-Xmx')), None)
                xms_arg = next((arg for arg in java_args if arg.startswith('-Xms')), None)

                height = target_profile['resolution']['height']
                width = target_profile['resolution']['width']

                if not xmx_arg or not xms_arg or not height or not width:
                    show_end_alert("No se encontraron valores por defecto para iniciar el perfil\n"
                                   "Se necesita iniciar el perfil a mano en CurseForge al menos una vez")

                
                default_profile = {
                    "profiles" : {
                        instance_name : {
                            "created" : current_time,
                            "gameDir" : f"{CF_instnace_path}\\",
                            "javaArgs" : (f"{xmx_arg} "
                                          f"{xms_arg} "
                                          f"-Dminecraft.applet.TargetDirectory=\"{CF_instnace_path}\" "
                                          "-Dfml.ignorePatchDiscrepancies=true "
                                          "-Dfml.ignoreInvalidMinecraftCertificates=true "
                                          "-Duser.language=en -Duser.country=US "
                                          f"-DlibraryDirectory=\"{CF_install_path}\\libraries\""),
                            "lastUsed" : current_time,
                            "lastVersionId" : "forge-43.4.0",
                            "name" : instance_name,
                            "resolution" : {
                                "height" : height,
                                "width" : width
                            },
                            "type" : "custom"
                        }
                    },
                    "settings" : {"crashAssistance" : False, "enableAdvanced" : False, "enableAnalytics" : False, "enableHistorical" : False, 
                                  "enableReleases" : True, "enableSnapshots" : False, "keepLauncherOpen" : False, "profileSorting" : "ByLastPlayed", 
                                  "showGameLog" : False, "showMenu" : False, "soundOn" : False
                    },
                    "version" : 3
                }
                show_end_alert("Perfil no encontrado y archivo de copia no existente --> comenzando con un perfil por defecto:\n"
                               "Memoria asignada y resolución tomada de la configuración de un perfil ya existente\n"
                               "Aún así se recomienda iniciar el perfil desde CurseForge al menos una vez", error=False)
                
                with open(profiles_path, 'w') as f:
                    json.dump(default_profile, f, indent=2)
                
                shutil.copy2(profiles_path, old_profiles_path)

    except FileNotFoundError:
        show_end_alert(f"No se encontró el archivo '{profiles_path}'")
    except json.JSONDecodeError:
        show_end_alert("No se pudo decodificar el archivo JSON.")
    except shutil.SameFileError:
        show_end_alert("El archivo de origen y destino son el mismo.")
    except PermissionError:
        show_end_alert("No se tienen permisos para crear el archivo de copia.")
    except Exception as e:
        show_end_alert(f"Error inesperado al crear la copia: {e}")


def git_management():
    try:
        if not CF_instnace_path.joinpath(".git").exists() or not CF_instnace_path.joinpath(".first_time").exists():
            for p in CF_instnace_path.rglob("*"):
                p.chmod(0o777)

            for dir in git_dirs:
                path = CF_instnace_path / dir
                if path.exists():
                    if path.is_dir():
                        shutil.rmtree(path)
                    else:
                        path.unlink()
            
            CF_instnace_path.joinpath(".first_time").touch()

            print(f"Inicializando un nuevo repositorio en {CF_instnace_path}.")
            repo = Repo.init(CF_instnace_path)
            
        else:
            repo = Repo(CF_instnace_path)

        if 'origin' not in [remote.name for remote in repo.remotes]:
            print(f"Agregando remoto '{git_repo}' como 'origin'.")
            repo.create_remote('origin', git_repo)

        print(f"Haciendo fetch del remoto 'origin'.")
        repo.remotes.origin.fetch()

        # print("Limpiando el repositorio local...")
        # repo.git.clean('-fd')

        if len(repo.heads) == 0:
            print("El repositorio local no tiene commits, reseteando a la rama remota 'main'.")
            repo.git.reset('--hard', 'origin/main')
        else:
            print("Restaurando el estado del repositorio...")
            repo.git.restore('--source', 'origin/main', '--staged', '--worktree', '.')

            print(f"Haciendo pull desde 'origin/main'.")
            repo.git.pull('origin', 'main')

    except InvalidGitRepositoryError:
        show_end_alert("Directorio no contiene un repositorio Git válido")
    except GitCommandError as e:
        show_end_alert(f"Error al ejecutar un comando Git: {e}")
    except Exception as e:
        show_end_alert(f"Error inesperado: {e}")

 
def main():
    initializate()
    profiles_management()
    git_management()

    subprocess.run(command_list)


if __name__ == "__main__":
    main()
