import os
import time
import sys
import glob
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
import selenium
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import datetime

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from shutil import copyfile, rmtree

from celery.contrib.testing.worker import start_worker
from django.core.management import call_command
from django.contrib.auth.models import User, Group
from .models import *

dir_path = os.path.dirname(os.path.realpath(__file__))

tests_dir = os.path.join('/'.join(__file__.split('/')[:-1]), "tests/")
SCR_DIR = os.path.join(tests_dir, "scr")
RESULTS_DIR = os.path.join(tests_dir, "results")
CLUSTER_DIR = os.path.join(tests_dir, "cluster")
KEYS_DIR = os.path.join(tests_dir, "keys")

from calcus.celery import app
class CalcusLiveServer(StaticLiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.driver = webdriver.Chrome()
        cls.driver.set_window_size(1424, 768)

        app.loader.import_module('celery.contrib.testing.tasks')
        cls.celery_worker = start_worker(app, perform_ping_check=False)
        cls.celery_worker.__enter__()

        if not os.path.isdir(SCR_DIR):
            os.mkdir(SCR_DIR)
        if not os.path.isdir(RESULTS_DIR):
            os.mkdir(RESULTS_DIR)
        if not os.path.isdir(CLUSTER_DIR):
            os.mkdir(CLUSTER_DIR)
            os.mkdir(os.path.join(CLUSTER_DIR, 'todo'))
            os.mkdir(os.path.join(CLUSTER_DIR, 'done'))
        if not os.path.isdir(KEYS_DIR):
            os.mkdir(KEYS_DIR)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()
        super().tearDownClass()
        cls.celery_worker.__exit__(None, None, None)

        if os.path.isdir(SCR_DIR):
            rmtree(SCR_DIR)
        if os.path.isdir(RESULTS_DIR):
            rmtree(RESULTS_DIR)
        if os.path.isdir(CLUSTER_DIR):
            rmtree(CLUSTER_DIR)
        if os.path.isdir(KEYS_DIR):
            rmtree(KEYS_DIR)

    def setUp(self):
        call_command('init_static_obj')
        self.username = "Selenium"
        self.password = "test1234"

        u = User.objects.create_superuser(username=self.username, password=self.password)#Weird things happen if the user is not superuser...
        u.save()
        self.login(self.username, self.password)
        self.profile = Profile.objects.get(user__username=self.username)

    def tearDown(self):
        for method, error in self._outcome.errors:
            if error:
                test_method_name = self._testMethodName
                self.driver.get_screenshot_as_file("{}/selenium_screenshots/{}.png".format(dir_path, test_method_name))

    def login(self, username, password):
        self.driver.get('{}/accounts/login/'.format(self.live_server_url))

        element = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "id_username"))
        )
        element = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "id_password"))
        )

        username_f = self.driver.find_element_by_id('id_username')
        password_f = self.driver.find_element_by_id('id_password')
        submit = self.driver.find_element_by_xpath('/html/body/div/div[2]/div/section/div[1]/div/form/div[2]/input[1]')
        username_f.send_keys(username)
        password_f.send_keys(password)
        submit.send_keys(Keys.RETURN)

        element = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "projects_list"))
        )

    def logout(self):
        self.driver.get('{}/accounts/logout/?next=/'.format(self.live_server_url))

    def lget(self, url):
        self.driver.get('{}{}'.format(self.live_server_url, url))

    def get_charge(self, fname):
        charge = 0
        if fname.find("anion"):
            charge = -1
        elif fname.find("dianion"):
            charge = -2
        elif fname.find("cation"):
            charge = 1
        elif fname.find("dication"):
            charge = 2

        return charge, fname.replace('dianion', '').replace('dication', '').replace('anion', '').replace('cation', '')

    def calc_input_params(self, params):
        self.driver.implicitly_wait(10)
        if 'calc_name' in params.keys():
            element = WebDriverWait(self.driver, 2).until(
                EC.presence_of_element_located((By.NAME, "calc_name"))
            )
            name_input = self.driver.find_element_by_name('calc_name')

        element = WebDriverWait(self.driver, 2).until(
            EC.presence_of_element_located((By.NAME, "calc_solvent"))
        )

        element = WebDriverWait(self.driver, 2).until(
            EC.presence_of_element_located((By.NAME, "calc_project"))
        )

        solvent_input = self.driver.find_element_by_name('calc_solvent')
        charge_input = self.driver.find_element_by_name('calc_charge')
        project_input = self.driver.find_element_by_id('calc_project')
        new_project_input = self.driver.find_element_by_name('new_project_name')
        calc_type_input = self.driver.find_element_by_id('calc_type')
        ressource_input = self.driver.find_element_by_name('calc_ressource')
        try:
            upload_input = self.driver.find_element_by_name('file_structure')
        except selenium.common.exceptions.NoSuchElementException:
            pass

        if 'calc_name' in params.keys():
            name_input.send_keys(params['calc_name'])

        if 'solvent' in params.keys():
            self.driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/form/div[2]/div[2]/div/div/div/select/option[text()='{}']".format(params['solvent'])).click()

        if 'charge' in params.keys():
            self.driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/form/div[2]/div[3]/div/div/div/select/option[text()='{}']".format(params['charge'])).click()

        if 'software' in params.keys():
            select = self.driver.find_element_by_id("calc_software")
            self.driver.execute_script("showDropdown = function (element) {var event; event = document.createEvent('MouseEvents'); event.initMouseEvent('mousedown', true, true, window); element.dispatchEvent(event); }; showDropdown(arguments[0]);",select)
            time.sleep(0.1)
            select.find_element_by_xpath("option[text()='{}']".format(params['software'])).click()

            #self.driver.find_element_by_xpath("//*[@id='calc_software']/option[text()='{}']".format(params['software'])).click()

        if 'type' in params.keys():
            self.driver.find_element_by_xpath("//*[@id='calc_type']/option[text()='{}']".format(params['type'])).click()

        if 'project' in params.keys():
            self.driver.find_element_by_xpath("//*[@id='calc_project']/option[text()='{}']".format(params['project'])).click()

        if 'new_project_name' in params.keys():
            new_project_input.send_keys(params['new_project_name'])

        if 'in_file' in params.keys():
            upload_input.send_keys("{}/tests/{}".format(dir_path, params['in_file']))

        if 'constraints' in params.keys():
            assert params['type'] == 'Constrained Optimisation'
            #[['Scan', 'Distance', [1, 3], [3.5, 1.5, 20]]].
            def handle_constraint(constraint, ind):
                c_mode = constraint[0]
                select = self.driver.find_element_by_id("constraint_mode_{}".format(ind))
                self.driver.execute_script("showDropdown = function (element) {var event; event = document.createEvent('MouseEvents'); event.initMouseEvent('mousedown', true, true, window); element.dispatchEvent(event); }; showDropdown(arguments[0]);",select)
                time.sleep(0.1)
                select.find_element_by_xpath("option[text()='{}']".format(c_mode)).click()

                c_type = constraint[1]
                select = self.driver.find_element_by_id("constraint_type_{}".format(ind))
                self.driver.execute_script("showDropdown = function (element) {var event; event = document.createEvent('MouseEvents'); event.initMouseEvent('mousedown', true, true, window); element.dispatchEvent(event); }; showDropdown(arguments[0]);",select)
                time.sleep(0.1)
                select.find_element_by_xpath("option[text()='{}']".format(c_type)).click()

                atoms = constraint[2]
                self.driver.find_element_by_id("calc_constraint_{}_1".format(ind)).send_keys(str(atoms[0]))
                self.driver.find_element_by_id("calc_constraint_{}_2".format(ind)).send_keys(str(atoms[1]))
                if c_type == 'Angle':
                    self.driver.find_element_by_id("calc_constraint_{}_3".format(ind)).send_keys(str(atoms[2]))
                elif c_type == 'Dihedral':
                    self.driver.find_element_by_id("calc_constraint_{}_3".format(ind)).send_keys(str(atoms[2]))
                    self.driver.find_element_by_id("calc_constraint_{}_4".format(ind)).send_keys(str(atoms[3]))
                if c_mode == "Scan":
                    scan = constraint[3]
                    self.driver.find_element_by_id("calc_scan_{}_1".format(ind)).send_keys(str(scan[0]))
                    self.driver.find_element_by_id("calc_scan_{}_2".format(ind)).send_keys(str(scan[1]))
                    self.driver.find_element_by_id("calc_scan_{}_3".format(ind)).send_keys(str(scan[2]))


            constr = params['constraints']
            handle_constraint(constr[0], 1)
            if len(constr) > 1:
                ind = 2
                for c in params['constraints'][1:]:
                    #click add
                    handle_constraint(c)
                    ind += 1


        if 'theory' in params.keys():
            select = self.driver.find_element_by_id("calc_theory_level")
            self.driver.execute_script("showDropdown = function (element) {var event; event = document.createEvent('MouseEvents'); event.initMouseEvent('mousedown', true, true, window); element.dispatchEvent(event); }; showDropdown(arguments[0]);",select)
            time.sleep(0.1)
            self.driver.find_element_by_xpath("//*[@id='calc_theory_level']/option[text()='{}']".format(params['theory'])).click()

        if 'method' in params.keys():
            self.driver.find_element_by_xpath("//*[@id='calc_method']/option[text()='{}']".format(params['method'])).click()

        if 'functional' in params.keys():
            element = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.ID, "calc_functional"))
            )

            self.driver.find_element_by_id("calc_functional").send_keys(params['functional'])

        if 'basis_set' in params.keys():
            self.driver.find_element_by_id("calc_basis_set").send_keys(params['basis_set'])

        if 'misc' in params.keys():
            self.driver.find_element_by_id("calc_misc").send_keys(params['misc'])

    def calc_launch(self):
        submit = self.driver.find_element_by_id('submit_button')
        submit.click()

    def get_number_calc_orders(self):
        assert self.is_on_page_calculations()
        calculations_container = self.driver.find_element_by_id("calculations_list")
        try:
            calculations_div = calculations_container.find_element_by_css_selector(".grid")
        except selenium.common.exceptions.NoSuchElementException:
            assert calculations_container.text.find('No calculation') != -1
            return 0

        calculations = calculations_div.find_elements_by_css_selector("article")
        num = len(calculations)
        return num

    def get_number_calc_methods(self):
        assert self.is_on_page_ensemble()

        tabs_list = self.driver.find_element_by_css_selector("#tabs")
        tabs = tabs_list.find_elements_by_css_selector("li")
        return len(tabs)

    def click_calc_method(self, num):
        assert self.is_on_page_ensemble()

        tabs_list = self.driver.find_element_by_css_selector("#tabs")
        tabs = tabs_list.find_elements_by_css_selector("li")
        tabs[num-1].click()

    def get_number_conformers(self):
        assert self.is_on_page_ensemble()
        conf_table = self.driver.find_element_by_id("conf_table")
        conformers = conf_table.find_elements_by_css_selector("tr")
        return len(conformers)

    def get_split_url(self):
        return self.driver.current_url.split('/')[3:]

    def get_group_panel(self):
        return self.driver.find_element_by_xpath("/html/body/article")

    def group_panel_present(self):
        try:
            a = self.get_group_panel()
        except selenium.common.exceptions.NoSuchElementException:
            return False
        else:
            return True

    def group_num_members(self):
        assert self.group_panel_present()

        panel = self.get_group_panel()
        users = panel.find_elements_by_css_selector(".panel-block")

        assert len(users) > 0

        return len(users)

    def group_click_member(self, name):
        assert self.group_panel_present()

        panel = self.get_group_panel()
        users = panel.find_elements_by_css_selector(".panel-block")

        for u in users:
            username = u.text
            if username == name:
                button = u.find_element_by_css_selector("a.button")
                button.click()
                return
    def is_user(self, username):
        try:
            u = Profile.objects.get(user__username=username)
        except Profile.DoesNotExist:
            return False
        else:
            return True

    def is_user_project(self, username, project_name):
        try:
            u = Profile.objects.get(user__username=username)
        except Profile.DoesNotExist:
            return False
        else:
            try:
                p = Project.objects.get(name=project_name.replace('%20', ' '), author=u)
            except Project.DoesNotExist:
                return False
            else:
                return True

    def is_molecule_id(self, mol_id):
        try:
            mol = Molecule.objects.get(pk=mol_id)
        except Molecule.DoesNotExist:
            return False
        else:
            return True

    def is_ensemble_id(self, e_id):
        try:
            e = Ensemble.objects.get(pk=e_id)
        except Ensemble.DoesNotExist:
            return False
        else:
            return True

    def is_on_page_projects(self):
        url = self.get_split_url()
        if (url[0] == 'projects' or url[0] == 'home') and (url[1] == '' or self.is_user(url[1])):
            return True
        else:
            return False

    def is_on_page_user_project(self):
        url = self.get_split_url()
        if url[0] == 'projects' and self.is_user(url[1]) and self.is_user_project(url[1], url[2]):
            return True
        else:
            return False

    def is_on_page_calculations(self):
        url = self.get_split_url()
        if url[0] == 'calculations' and url[1] == '':
            return True
        else:
            return False

    def is_on_page_profile(self):
        url = self.get_split_url()
        if url[0] == 'profile' and url[1] == '':
            return True
        else:
            return False

    def is_on_page_managePI(self):
        url = self.get_split_url()
        if url[0] == 'manage_pi_requests' and url[1] == '':
            return True
        else:
            return False

    def is_on_page_molecule(self):
        url = self.get_split_url()

        try:
            mol_id = int(url[1])
        except:
            return False

        if url[0] == 'molecule' and self.is_molecule_id(mol_id):
            return True
        else:
            return False

    def is_on_page_ensemble(self):
        url = self.driver.current_url.split('/')[3:]

        try:
            e_id = int(url[1])
        except:
            return False

        if url[0] == 'ensemble' and self.is_ensemble_id(e_id):
            return True
        else:
            return False

    def get_number_projects(self):
        assert self.is_on_page_projects()

        project_div = self.driver.find_element_by_css_selector(".grid")
        projects = project_div.find_elements_by_css_selector("article")
        num = len(projects)
        if num == 0:
            assert project_div.text.find('No project') != -1
        return num

    def click_project(self, name):
        assert self.is_on_page_projects()

        project_div = self.driver.find_element_by_css_selector(".grid")
        projects = project_div.find_elements_by_css_selector("article")

        for proj in projects:
            p_name = proj.find_element_by_css_selector("div > p").text
            if p_name == name:
                proj.click()
                return

    def get_number_molecules(self):
        assert self.is_on_page_user_project()

        molecules_div = self.driver.find_element_by_css_selector(".grid")
        molecules = molecules_div.find_elements_by_css_selector("article")
        num = len(molecules)
        if num == 0:
            assert molecules_div.text.find('No molecule') != -1
        return num

    def click_molecule(self, name):
        assert self.is_on_page_user_project()

        molecules_div = self.driver.find_element_by_css_selector(".grid")
        molecules = molecules_div.find_elements_by_css_selector("article")

        for mol in molecules:
            mol_name = mol.find_element_by_css_selector("div > p").text
            if mol_name == name:
                mol.click()
                return

    def get_number_ensembles(self):
        assert self.is_on_page_molecule()

        ensembles_div = self.driver.find_element_by_css_selector(".grid")
        ensembles = ensembles_div.find_elements_by_css_selector("article")
        num = len(ensembles)
        if num == 0:
            assert ensembles_div.text.find('No ensemble') != -1
        return num

    def click_ensemble(self, name):
        assert self.is_on_page_molecule()

        ensembles_div = self.driver.find_element_by_css_selector(".grid")
        ensembles = ensembles_div.find_elements_by_css_selector("article")

        for e in ensembles:
            e_name = e.find_element_by_css_selector("div > p").text
            if e_name == name:
                e.click()
                return

        raise EnsembleNotFound

    def click_latest_calc(self):
        assert self.is_on_page_calculations()
        assert self.get_number_calc_orders() > 0

        calculations_container = self.driver.find_element_by_id("calculations_list")
        calculations_div = calculations_container.find_element_by_css_selector(".grid")
        calculations = calculations_div.find_elements_by_css_selector("article")
        calculations[0].click()

    def apply_PI(self, group_name):
        assert self.is_on_page_profile()
        group_name = self.driver.find_element_by_name('group_name')
        submit = self.driver.find_element_by_xpath('/html/body/div/div[2]/div/div[1]/form/button')
        group_name.send_keys("Test group")
        submit.send_keys(Keys.RETURN)

        element = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "PI_application_message"))
        )


    def accept_PI_request(self):
        assert self.is_on_page_managePI()
        element = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "table"))
        )

        table = self.driver.find_element_by_class_name('table')

        self.assertTrue(table.text.find("Accept") != -1)
        self.assertTrue(table.text.find("Deny") != -1)

        accept_button = self.driver.find_element_by_xpath('/html/body/div/div/table/tbody/tr[1]/td[1]/button')
        accept_button.send_keys(Keys.RETURN)

    def wait_latest_calc_done(self, timeout):
        assert self.is_on_page_calculations()
        assert self.get_number_calc_orders() > 0


        ind = 0
        while ind < timeout:
            calculations_container = self.driver.find_element_by_id("calculations_list")
            calculations_div = calculations_container.find_element_by_css_selector(".grid")
            calculations = calculations_div.find_elements_by_css_selector("article")
            header = calculations[0].find_element_by_class_name("message-header")
            if "has-background-success" in header.get_attribute("class") or "has-background-danger" in header.get_attribute("class"):
                    return
            time.sleep(2)
            ind += 2
            self.driver.refresh()

    def latest_calc_successful(self):
        assert self.is_on_page_calculations()
        assert self.get_number_calc_orders() > 0


        calculations_container = self.driver.find_element_by_id("calculations_list")
        calculations_div = calculations_container.find_element_by_css_selector(".grid")
        calculations = calculations_div.find_elements_by_css_selector("article")
        header = calculations[0].find_element_by_class_name("message-header")
        return "has-background-success" in header.get_attribute("class")

    def add_user_to_group(self, username):
        assert self.is_on_page_profile()

        element = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "code"))
        )
        element = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "user_to_add"))
        )


        p = Profile.objects.get(user__username=username)
        code = p.code
        field_username = self.driver.find_element_by_id("user_to_add")
        field_code = self.driver.find_element_by_id("code")
        button_submit = self.driver.find_element_by_xpath("/html/body/div/div[3]/div/div/div[1]/div/button")
        field_username.send_keys(username)
        field_code.send_keys(code)
        button_submit.send_keys(Keys.RETURN)

    def launch_ensemble_next_step(self):
        assert self.is_on_page_ensemble()
        button = self.driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div[1]/a")
        button.click()

    def launch_structure_next_step(self):
        assert self.is_on_page_ensemble()
        button = self.driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div[1]/button[5]")
        button.click()

    def delete_project(self, name):
        assert self.is_on_page_projects()
        main_window_handle = None
        while not main_window_handle:
            main_window_handle = self.driver.current_window_handle

        project_div = self.driver.find_element_by_css_selector(".grid")
        projects = project_div.find_elements_by_css_selector("article")

        for proj in projects:
            p_name = proj.find_element_by_css_selector("div > p").text
            if p_name == name:
                trash = proj.find_element_by_css_selector(".message-header > div > a > i.fa-trash-alt")
                trash.click()

                alert = self.driver.switch_to_alert()
                alert.accept()
                self.driver.switch_to_default_content()
                return

    def delete_molecule(self, name):
        assert self.is_on_page_user_project()
        main_window_handle = None
        while not main_window_handle:
            main_window_handle = self.driver.current_window_handle

        molecule_div = self.driver.find_element_by_css_selector(".grid")
        molecules = molecule_div.find_elements_by_css_selector("article")

        for mol in molecules:
            mol_name = mol.find_element_by_css_selector("div > p").text
            if mol_name == name:
                trash = mol.find_element_by_css_selector(".message-header > div > a > i.fa-trash-alt")
                trash.click()

                alert = self.driver.switch_to_alert()
                alert.accept()
                self.driver.switch_to_default_content()
                return

    def delete_ensemble(self, name):
        assert self.is_on_page_molecule()
        main_window_handle = None
        while not main_window_handle:
            main_window_handle = self.driver.current_window_handle

        ensemble_div = self.driver.find_element_by_css_selector(".grid")
        ensembles = ensemble_div.find_elements_by_css_selector("article")

        for e in ensembles:
            e_name = e.find_element_by_css_selector("div > p").text
            if e_name == name:
                trash = e.find_element_by_css_selector(".message-header > div > a > i.fa-trash-alt")
                trash.click()

                alert = self.driver.switch_to_alert()
                alert.accept()
                self.driver.switch_to_default_content()
                return

    def setup_test_group(self):
        self.lget('/profile/')

        self.apply_PI("Test group")
        self.logout()

        u = User.objects.create_superuser(username="SU", password=self.password)
        u.save()
        p = Profile.objects.get(user__username="SU")
        p.save()

        self.login("SU", self.password)
        self.lget('/manage_pi_requests/')

        self.accept_PI_request()
        self.logout()

        self.login(self.username, self.password)
        u = User.objects.create_user(username="Student", password=self.password)
        self.lget("/profile/")
        self.add_user_to_group("Student")

    def is_loaded_frequencies(self):
        assert self.is_on_page_ensemble()

        try:
            freq_div = self.driver.find_element_by_id("frequency_structure_details")
        except selenium.common.exceptions.NoSuchElementException:
            return False
        table = self.driver.find_element_by_css_selector(".column:nth-child(2) > table")

        try:
            table2 = self.driver.find_element_by_id("vib_table")
        except selenium.common.exceptions.NoSuchElementException:
            return False

        rows = table.find_elements_by_css_selector("tr")

        if len(rows) > 0:
            return True
        return False

    def is_loaded_mo(self):
        assert self.is_on_page_ensemble()

        try:
            mo_div = self.driver.find_element_by_id("mo_structure_details")
        except selenium.common.exceptions.NoSuchElementException:
            return False

        try:
            mo_viewer = mo_div.find_element_by_id("mo_viewer_div")
            mo_container = mo_div.find_element_by_id("mo_container")
        except selenium.common.exceptions.NoSuchElementException:
            return False

        return True
