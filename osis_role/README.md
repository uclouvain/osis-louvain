# OSIS Role

`OSIS Role` is a Django application to manage access management accros OSIS plateform.
`OSIS Role` is based on default access management provided by [Django Framework (RBAC)](https://docs.djangoproject.com/fr/2.2/ref/contrib/auth/)  and 
[rules (ABAC)](https://github.com/dfunckt/django-rules).

Table of Contents
=================

- [Requirements](#requirements)  
- [How to install ?](#how-to-install)  
  - [Install requirements](#install-requirements)  
  - [Configuring Django](#configuring-django)  
- [Using OSIS-Role](#using-osis-role)
  - [Creating role](#create-role)
  - [Manage permissions within role](#permissions-in-role)
  - [Permissions in views](#permissions-in-views)
  - [Permissions in code](#permissions-in-code)
  - [Error management](#error-management)
  - [Template Tags](#template-tags)
  - [Synchronize RBAC <> ABAC](#synchronize-rbac--abac)
- [Managing OSIS-Role](#osis-role-management)
  - [Via administration](#via-administration)
  - [Via interface](#via-interface)
 
 
Requirements
===========

- `OSIS Role` required `Django Framework` 2.2.0
- `OSIS Role` required `rules` 2.2.10

How to install ?
================

Install requirements
--------------------
Using pip:
```
    $ pip install -r requirements.txt
```

Configuring Django
------------------

Add ``osis_role`` to ``INSTALLED_APPS``:

    INSTALLED_APPS = (
        ...
        'osis_role',
        ...
    )

Add the authentication backend:

    AUTHENTICATION_BACKENDS = (
        'osis_role.contrib.permissions.ObjectPermissionBackend'
    )
    
  *OR*
  
  Add line in .env:
        
    AUTHENTICATION_BACKENDS = 'osis_role.contrib.permissions.ObjectPermissionBackend'

Using OSIS-Role
===============
`osis_role` is based on the idea that you register supported roles within a Django application. 
On each role, we declare a dict-like object that maps string keys used as identifiers of business 
action to a set of `Predicates`

Creating role
-------------

To declare a role within a Django application:
 
  
 - Create a class - *corresponding to role* - on models package

        import rules
        from django.utils.translation import gettext_lazy as _     
        from osis_role.contrib import models as osis_role_models
         
        class Student(osis_role_models.RoleModel):
            class Meta:
                verbose_name = _("Student")
                verbose_name_plural = _("Students")
                group_name = "students"   # Django group name corresponding
            
            @classmethod
            def rule_set(cls):
                return rules.RuleSet({
                    'view_examscore': examscore_period_is_open & student_is_registered_to_exam,
                    ...            
                })
                           
            
 - Create a package, __called roles__, at the root of the app 
 
        <app_name>
        | api
          |__ #...
        | #...
        | roles.py
        
 - Register the role previously created on __roles__ package
 
        from base.models import student
        from osis_role import role
         
        role.role_manager.register(student.Student)
      
        
Manage permissions within role
-------------------------------
All permissions for a specific role are contained in class method `rule_set(cls)`
These permissions are specified as predicates.
This method must return an RuleSet object provided by `rules` library.

Documentation: [How to write predicate ?](https://github.com/dfunckt/django-rules/blob/master/README.rst#setting-up-rules)

`osis_role` provide a [context](https://github.com/dfunckt/django-rules/blob/master/README.rst#invocation-context) with queryset of the role accessible on every predicate

-       from rules import predicate

        @predicate(bind=True)
        def is_linked_to_management_entity(self, user, obj):
            role_qs = self.context['role_qs']       # role_qs is already filtered by connected user
            return role_qs.filter(entity=obj.management_entity_id).exists()

Permissions in views
--------------------
`osis_role` is based on `rules` package and `rules` comes with a set of view decorators to help you enforce authorization in your views.
`osis_role` wraps some functionalities of rules.


Documentation: [How to protect views ?](https://github.com/dfunckt/django-rules/blob/master/README.rst#permissions-in-views)

<ins>Class Based View style: </ins>
-       from osis_role.contrib.views import PermissionRequiredMixin
        ...
        
        class CreateObject(PermissionRequiredMixin, CreateView):
            ....
            permission_required = 'base.add_object'
            ....
            
            def get_permission_object(self):
                # Default behaviour and can be overrided
                return self.get_object()

<ins>Function Based View style: </ins>
-       from osis_role.contrib.views import permission_required
        ...

        def get_object_by_pk(request, object_id):
            return get_object_or_404(
                ObjectModel.objects.select_related(...),
                pk=object_id,
            )

        @permission_required('base.change_educationgroup', fn=get_object_by_pk)
        def create_object(request, object_id):
            ....
            
            

Permissions in code
--------------------

`osis_role` is based on the default auth module provided by Django. 

If you want to test if a user has permission, you can use has_perm method provided in User Model:

-       def can_access_obj(user, obj):
            return user.has_perm("base.view_object", obj)

Error management
----------------

`osis_role` uses an `error` module which manage error related to a specific permission.

`osis_role` provides a decorator which allow you to set permission message on rules precidate.

-       from rules import predicate
        from osis_role.errors import predicate_failed_msg

        @predicate(bind=True)
        @predicate_failed_msg(message="You don't have access because not linked to management entity")
        def is_linked_to_management_entity(self, user, obj):
            role_qs = self.context['role_qs']       # role_qs is already filtered by connected user
            return role_qs.filter(entity=obj.management_entity_id).exists()



If you want to dynamically set the error message, you can use :

-       errors.set_permission_error(user, perm_name, custom_msg)

This method should be called when a user does not fulfill a required permission, as in this example:

-       from osis_role import errors

        def update_object(user, object):
            perm_name = "base.view_object"
            has_perm = user.has_perm(perm_name, object)
            if not has_perm:
                errors.set_permission_error(user, perm_name, ""You don't have access")
            return has_perm


Template tags
-------------

`osis_role` provide multiples templatetags 

- <b>a_tag_has_perm</b>: Display <a/> tag with error message as a tooltip when permission denied
        
        {% load osis_role %}
        .......
        <div>
             {% a_tag_has_perm create_obj_url _('New Object') 'base.add_obj' user %}                    
        </div>

- <b>a_tag_modal_has_perm</b>: same as a_tag_has_perm but load url into a modal
        
       {% load osis_role %}
        .......
        <div>
             {% a_tag_modal_has_perm create_obj_url _('New Object') 'base.add_obj' user %}                    
        </div>

- <b>has_perm</b>: Evaluate permission according to user and ressource
        
        {% load osis_role %}
        .......
        {% has_perm 'base.change_obj' user obj as can_change_obj %}
        {% if can_change_obj %}
            <button>Edit Object</button>
        {% endif %}

- <b>has_module_perms</b>: Evaluate if there is at least one permission valid within an application

        {% load osis_role %}
        .......
        {% has_module_perms user 'base' as can_access_base_app %}
        {% if can_access_base_app %}
            <ul> 
                <li>Create Object</li>
                <li> ... </li>
                ...
            </ul>
        {% endif %}


Synchronize RBAC <> ABAC
------------------------

`osis_role` provide two usefull commands that help synchronization between Django `Groups` and `Role` registered:

1. Synchronization between permission used in registered `Role` (_= keys of RuleSet_)  and permissions contained in `Groups`       
      
       $ python manage.py sync_perm_role
    
2. Synchronize all declared osis-roles (_= Groups_) with user in table which are defined in OsisRoleManager       
      
       $ python manage.py sync_user_role


Managing OSIS-Role
==================

Via administration
------------------

**/!\ Don't asign groups which are managed by OSIS-Role directly in Users admin interface !**

In order to keep synchronization between RBAC <> ABAC, you **must** add a person on a role via AdminRoleModel related 
or via [interface](#via-interface)

Via interface
-------------

TODO

FAQ
===
- ##### Can I use a Django Group without registering a corresponding role ? 
   Yes, `osis_role` fallback to standard behaviour when no corresponding roles found on RoleManager
   